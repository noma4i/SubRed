import sublime, sublime_plugin, os, sys, imp

sys.path.append(os.path.join(os.path.dirname(__file__), "libs"))


from redmine import Redmine

class RedClient(object):
  def __init__(self, edit):
    settings = self.settings()
    self.__url  = settings.get('redmine_url')
    self.__api_key  = settings.get('api_key')
    self.__build()

  def __build(self):
    redmine = Redmine(self.__url, key=self.__api_key)
    # issue = red_mine.issues
    issue = redmine.issue.get(22245)
    print(dir(issue))
    print(issue.description)
    self.scratch(issue.description, title="Redmine Issue"+str(issue.id))

  def settings(self):
    return sublime.load_settings("RedClient.sublime-settings")

  def get_window(self):
    return sublime.active_window()

  def scratch(self, output, title=False, position=None, **kwargs):
    scratch_file = self.get_window().new_file()
    if title:
        scratch_file.set_name(title)
    scratch_file.set_scratch(True)
    scratch_file.insert(edit, 0, output)

    scratch_file.set_read_only(True)

    return scratch_file
  def _output_to_view(self, output_file, output, clear=False, syntax="Packages/Diff/Diff.tmLanguage", **kwargs):
    output_file.set_syntax_file(syntax)
    edit = output_file.begin_edit()
    if clear:
        region = sublime.Region(0, self.output_view.size())
        output_file.erase(edit, region)
    output_file.insert(edit, 0, output)
    output_file.end_edit(edit)

class SubRedCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    RedClient(self)

    # self.view.replace(edit, sublime.Region(0, self.view.size()), text)
