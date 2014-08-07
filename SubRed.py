import sublime, sublime_plugin, os, sys, imp, re

sys.path.append(os.path.join(os.path.dirname(__file__), "libs"))


from redmine import Redmine

class SubRedCommand(sublime_plugin.WindowCommand):
  def run(self):
    self.window.show_input_panel("Isssue ID #:", "", self.get_issue, None, None)

  def get_issue(self,text):
    if self.window.active_view():
      self.window.active_view().run_command( 'redmine_fetcher', {'issue_id': text} )


class RedmineFetcherCommand(sublime_plugin.TextCommand):
  def run(self, edit, issue_id):
    settings = self.settings()
    self.__url  = settings.get('redmine_url')
    self.__api_key  = settings.get('api_key')

    redmine = Redmine(self.__url, key=self.__api_key)
    # 22245
    issue = redmine.issue.get(issue_id)
    self.redmine_view(edit, issue, title="Redmine Issue #"+str(issue.id))

  def settings(self):
    return sublime.load_settings("RedClient.sublime-settings")

  def get_window(self):
    return sublime.active_window()

  def redmine_view(self, edit, issue, title=False, position=None, **kwargs):
    syntax = 'Packages/Textile/Textile.tmLanguage'
    redmine_view = self.get_window().new_file()
    redmine_view.set_name(title)
    redmine_view.set_scratch(True)
    redmine_view.set_syntax_file(syntax)

    desc = issue.description.replace("\r", "")

    content = ''
    content += '**%s**' % desc
    redmine_view.insert(edit, 0, content)

    redmine_view.set_read_only(True)

    return redmine_view