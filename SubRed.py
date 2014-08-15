import sublime
import sublime_plugin
import os
import sys
import imp
import re
import webbrowser
import platform

sys.path.append(os.path.join(os.path.dirname(__file__), "libs"))

from redmine import Redmine

class SubRedmine:
  def connect():
    settings = sublime.load_settings("SubRed.sublime-settings")
    url  = settings.get('redmine_url')
    api_key  = settings.get('api_key')

    return Redmine(url, key=api_key)

# View Issue
class SubRedCommand(sublime_plugin.WindowCommand):
  def run(self):
    self.window.show_input_panel("Issue ID #:", "", self.get_issue, None, None)

  def get_issue(self,text):
    if self.window.active_view():
      self.window.active_view().run_command( 'redmine_fetcher', {'issue_id': text} )

# Redmine: Refresh Issue
class SubRedRefreshIssueCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    self.view.run_command( 'redmine_fetcher', {'issue_id': 'self'} )
    sublime.status_message('Issue Refreshed!')

# Redmine: List Queries
class SubRedGetQueryCommand(sublime_plugin.TextCommand):
  def run(self,edit):
    def on_done(i):
      if i > -1:
        query = query_ids[i]
        project_id = query_projects[i]
        self.view.run_command( 'redmine_fetch_query', {'project_id': project_id, 'query_id': query} )

    redmine = SubRedmine.connect()
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

# Redmine: Set Status
class SubRedSetStatusCommand(sublime_plugin.TextCommand):
  def run(self,edit):
    redmine = SubRedmine.connect()
    issue_id = self.view.name().replace('Redmine Issue #','')

    statuses = redmine.issue_status.all()
    statuses_names = []
    statuses_ids = []
    for status in statuses:
      statuses_names.append(status.name)
      statuses_ids.append(status.id)
    def on_done(i):
      if i > -1:
        if issue_id != 0:
          issue = redmine.issue.get(issue_id)
          issue.status_id = statuses_ids[i]
          issue.save()
          sublime.status_message('Issue #%r now is %s' % (issue.id, statuses_names[i]))
          self.view.run_command( 'redmine_fetcher', {'issue_id': issue_id} )
    if "Issue #" in self.view.name():
      self.view.window().show_quick_panel(statuses_names, on_done)
    else:
      sublime.message_dialog("Open Issue!")

# Redmine: Assigned To
class SubRedSetAssignedCommand(sublime_plugin.TextCommand):
  def run(self,edit):
    issue_id = self.view.name().replace('Redmine Issue #','')
    redmine = SubRedmine.connect()
    current_user = redmine.user.get('current')

    issue = redmine.issue.get(issue_id)
    issue.assigned_to_id = current_user.id
    issue.save()

    sublime.status_message('Issue #%r is assigned to you!' % issue.id)
    self.view.run_command( 'redmine_fetcher', {'issue_id': issue.id} )

# #Redmine: Open in Browser
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

########################## View Actions ##########################
class RedmineFetchQueryCommand(sublime_plugin.TextCommand):
  def run(self,edit,project_id,query_id):
    redmine = SubRedmine.connect()
    issues = redmine.issue.filter(project_id=project_id,query_id=query_id)
    self.redmine_view(edit, issues, title="Redmine Query List")

  def redmine_view(self, edit, issues, title):
    r = self.view.window().new_file()
    r.set_name(title)
    r.set_scratch(True)
    r.set_syntax_file('Packages/Markdown/Markdown.tmLanguage')

    content = 'Total: %s\n' % len(issues)
    content += '-------------------------------------------\n'
    for issue in issues:
      content += '#%r\t\t%s\n' % (issue.id,issue.subject)

    r.insert(edit, 0, content)
    r.set_read_only(True)

class RedmineFetcherCommand(sublime_plugin.TextCommand):
  def run(self, edit, issue_id):
    redmine = SubRedmine.connect()
    if issue_id == 'self':
      issue_id = self.view.name().replace('Redmine Issue #','')
    try:
      issue = redmine.issue.get(issue_id)
    except:
      sublime.status_message('Issue #%s not found!' % (issue_id))

    self.redmine_view(edit, issue, title="Redmine Issue #"+str(issue.id))

  def redmine_view(self, edit, issue, title):
    if self.view.name() == ("Redmine Issue #"+str(issue.id)):
      r = self.view
      r.set_read_only(False)
      r.erase(edit, sublime.Region(0, self.view.size()))
    else:
      r = sublime.active_window().new_file()
      r.set_name(title)
      r.set_scratch(True)
      r.set_syntax_file('Packages/Markdown/Markdown.tmLanguage')

    desc = issue.description.replace("\r", "").replace("\n","\n#|\t\t")

    content = '-------------------------------------------\n'
    content += '#Issue %s\n' % issue.id
    content += '###### Status:         %s\n' %issue.status
    content += '###### Priority:       %s\n' %issue.priority
    if hasattr(issue, 'assigned_to'):
      content += '###### Assigned to:    %s\n' %issue.assigned_to
    content += '# %s\n' % issue.subject
    content += '-------------------------------------------\n\n\n'

    if len(issue.attachments) > 0:
      content += '---'
    for f in issue.attachments:
      content += '\n#\t%r (%s)' % (f.filename,f.content_url)
    if len(issue.attachments) > 0:
      content += '\n---\n\n'

    content += '[%r](%s)' % (issue.created_on.strftime("%A %d. %B %Y"), issue.author.name)
    content += '\n#|\t\t%s\n\n\n' % desc
    for journal in issue.journals:
      if hasattr(journal, 'notes'):
        if journal.notes != '':
          content += '[%r](%s)\n' % (journal.created_on.strftime('%A %d. %B %Y'), journal.user)
          content += '\t%s\n' % journal.notes.replace('\r', '')
          content += '\n'

    r.insert(edit, 0, content)
    r.set_read_only(False)