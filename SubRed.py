import sublime, sublime_plugin, os, sys, imp, re, webbrowser, platform

sys.path.append(os.path.join(os.path.dirname(__file__), "libs"))


from redmine import Redmine

cached_issue_id = 0

class SubRedCommand(sublime_plugin.WindowCommand):
  def run(self):
    self.window.show_input_panel("Isssue ID #:", "", self.get_issue, None, None)

  def get_issue(self,text):
    if self.window.active_view():
      self.window.active_view().run_command( 'redmine_fetcher', {'issue_id': text} )

class SubRedGetQueryCommand(sublime_plugin.TextCommand):
  def run(self,edit):
    global project_id
    def on_done(i):
      if i > -1:
        query = query_ids[i]
        project_id = query_projects[i]
        self.view.run_command( 'redmine_query_list', {'project_id': project_id, 'query_id': query} )

    redmine = RedmineFetcherCommand.init_redmine(self)
    queries = redmine.query.all()
    query_names = []
    query_ids = []
    query_projects = []
    for query in queries:
      query_names.append(query.name)
      query_ids.append(query.id)
      if hasattr(query, 'project_id'):
        query_projects.append(query.project_id)
    self.view.window().show_quick_panel(query_names, on_done)


class RedmineQueryListCommand(sublime_plugin.TextCommand):
  def run(self,edit,project_id,query_id):
    redmine = RedmineFetcherCommand.init_redmine(self)
    issues = redmine.issue.filter(project_id=project_id,query_id=query_id)
    self.redmine_view(edit, issues, title="Redmine Query List")

  def redmine_view(self, edit, issues, title=False, position=None, **kwargs):
    syntax = 'Packages/Markdown/Markdown.tmLanguage'
    redmine_view = self.view.window().new_file()
    redmine_view.set_name(title)
    redmine_view.set_scratch(True)
    redmine_view.set_syntax_file(syntax)

    content = 'Total: %s\n' % len(issues)
    content += '-------------------------------------------\n'
    for issue in issues:
      content += '#%r\t\t%s\n' % (issue.id,issue.subject)

    redmine_view.insert(edit, 0, content)
    redmine_view.set_read_only(True)

    return redmine_view

class SubRedGoRedmineCommand(sublime_plugin.TextCommand):
  def run(self,edit):
    current_os = platform.system()
    settings = sublime.load_settings("SubRed.sublime-settings")
    issue_id = self.view.name().replace('Redmine Issue #','')
    if current_os == 'Darwin':
      wbrowser = webbrowser.get('macosx')
    elif current_os == 'Windows':
      wbrowser = webbrowser.get('windows-default')
    else:
      wbrowser = webbrowser.get('mozilla')

    if issue_id:
      url = settings.get('redmine_url')+"/issues/"+issue_id
      wbrowser.open_new(url)
    else:
      sublime.message_dialog("Open Issue!")

class SubRedSetStatusCommand(sublime_plugin.TextCommand):
  def run(self,edit):
    global cached_statuses, cached_issue_id
    redmine = RedmineFetcherCommand.init_redmine(self)
    statuses = redmine.issue_status.all()
    statuses_names = []
    statuses_ids = []
    for status in statuses:
      statuses_names.append(status.name)
      statuses_ids.append(status.id)

    def on_done(i):
      if i > -1:
        if cached_issue_id != 0:
          issue = redmine.issue.get(cached_issue_id)
          issue.status_id = statuses_ids[i]
          issue.save()
          sublime.status_message('Issue #%r now is %s' % (issue.id, statuses_names[i]))
          self.view.run_command( 'redmine_fetcher', {'issue_id': cached_issue_id} )

    region = sublime.Region(51,52)
    issue_line = self.view.window().active_view().line(region)
    issue_line_content = self.view.window().active_view().substr(issue_line)

    if "#Issue" in issue_line_content:
      cached_issue_id = issue_line_content.replace('#Issue ','')
      self.view.window().show_quick_panel(statuses_names, on_done)
    else:
      sublime.message_dialog("Open Issue!")


class RedmineFetcherCommand(sublime_plugin.TextCommand):
  def run(self, edit, issue_id):
    global cached_issue_id

    redmine = self.init_redmine()
    issue = redmine.issue.get(issue_id)
    self.redmine_view(edit, issue, title="Redmine Issue #"+str(issue.id))
    cached_issue_id = issue.id

  def init_redmine(self):
    settings = sublime.load_settings("SubRed.sublime-settings")
    url  = settings.get('redmine_url')
    api_key  = settings.get('api_key')

    return Redmine(url, key=api_key)

  def get_window(self):
    return sublime.active_window()

  def redmine_view(self, edit, issue, title=False, position=None, **kwargs):
    syntax = 'Packages/Markdown/Markdown.tmLanguage'
    if self.view.name() == ("Redmine Issue #"+str(issue.id)):
      redmine_view = self.view
      redmine_view.set_read_only(False)
      redmine_view.erase(edit, sublime.Region(0, self.view.size()))
    else:
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
    if hasattr(issue, 'assigned_to'):
      content += '###### Assigned to:    %s\n' %issue.assigned_to
    content += '# %s\n' % issue.subject
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