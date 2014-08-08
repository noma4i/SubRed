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
    try:
      issue = redmine.issue.get(issue_id)
      self.redmine_view(edit, issue, title="Redmine Issue #"+str(issue.id))
    except:
      sublime.message_dialog("No such issue")

  def settings(self):
    return sublime.load_settings("SubRed.sublime-settings")

  def get_window(self):
    return sublime.active_window()

  def redmine_view(self, edit, issue, title=False, position=None, **kwargs):
    syntax = 'Packages/Markdown/Markdown.tmLanguage'
    redmine_view = self.get_window().new_file()
    redmine_view.set_name(title)
    redmine_view.set_scratch(True)
    redmine_view.set_syntax_file(syntax)

    desc = issue.description.replace("\r", "")


    # -------------------------------------------
    # #Issue #22089
    # ###### Status:         QA Rejected
    # ###### Priority:       Low
    # ###### Assigned to:    Alex

    # -------------------------------------------

    content = '-------------------------------------------\n'
    content += '#Issue %s\n' % issue.id
    content += '###### Status:         %s\n' %issue.status
    content += '###### Priority:       %s\n' %issue.priority
    content += '###### Assigned to:    %s\n' %issue.assigned_to
    content += '-------------------------------------------\n\n\n'

    content += '[%r](%s)' % (issue.created_on.strftime("%A %d. %B %Y"), issue.author.name)
    content += '\n#|\t\t%s\n\n\n' % desc.replace("\n","\n#|\t\t")
    for journal in issue.journals:
      if hasattr(journal, 'notes'):
        if journal.notes != '':
          content += '[%r](%s)\n' % (journal.created_on.strftime('%A %d. %B %Y'), journal.user)
          content += '\t%s\n' % journal.notes.replace('\r', '')
          content += '\n'
    redmine_view.insert(edit, 0, content)

    redmine_view.set_read_only(True)

    return redmine_view