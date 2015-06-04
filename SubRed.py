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

projectsList = {}

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

# View current Issue
class SubRedCurrentCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    for region in self.view.sel():
      if region.empty():
        # Get the selected text
        issueNum = self.view.line(region)
        issueNum = self.view.substr(issueNum)
        issueNum = issueNum.split(' ')[0]
        if len(issueNum) > 0 :
          sublime.status_message('Openning issue ' + issueNum)
          issueNum = issueNum.replace('#', '')
          self.view.run_command( 'redmine_fetcher', {'issue_id': issueNum} )

# Process hotkeys for issue view
class SubRedProcessHotkeyCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    for region in self.view.sel():
      if region.empty():
        # Get the selected text
        identifier = self.view.line(region)
        identifier = self.view.substr(identifier)
        identifier = identifier.replace('#', '').strip()
        identifier = identifier.split(' ')
        if len(identifier) > 1:
          operation = identifier[0]
          object_id = identifier[1]
          if operation == 'Revision':
            project_id = identifier[2].replace('[ProjectId:','').rstrip(']')
            url = '/projects/{0}/repository/revisions/{1}/diff/'.format(project_id, object_id.lstrip('r'))
          self.view.run_command( 'sub_red_go_to_url', {'url': url, 'external': False} )


# Comment Issue
class SubRedCommentIssueCommand(sublime_plugin.WindowCommand):
  def run(self):
    self.window.show_input_panel("Comment #:", "", self.post_comment, None, None)

  def post_comment(self,text):
    self.window.active_view().run_command( 'redmine_post_comment', {'text': text} )

# Redmine: Refresh Issue
class SubRedRefreshIssueCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    self.view.run_command( 'redmine_fetcher', {'issue_id': 'self'} )
    sublime.status_message('Issue Refreshed!')

# Redmine: List Queries
class SubRedGetQueryCommand(sublime_plugin.TextCommand):
  def run(self,edit, project_id=None):
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
      if project_id is not None and project_id != query.project_id:
        continue;
      query_names.append(query.name)
      query_ids.append(query.id)
      if hasattr(query, 'project_id'):
        query_projects.append(query.project_id)

    self.view.window().show_quick_panel(query_names, on_done)

# Redmine: List Projects
class SubRedGetProjectsCommand(sublime_plugin.TextCommand):
  def run(self,edit):
    redmine = SubRedmine.connect()
    projects = redmine.project.all()

    self.redmine_view(edit, projects, title="Redmine Projects List")

  def redmine_view(self, edit, projects, title):
    if self.view.name() == title:
      r = self.view
      r.set_read_only(False)
      r.erase(edit, sublime.Region(0, self.view.size()))
    else:
      r = self.view.window().new_file()
      r.set_name(title)
      r.set_scratch(True)
      r.set_syntax_file('Packages/Markdown/Markdown.tmLanguage')
      r.settings().set('sub_list_projects', True)

    content = ">> ['enter - list queries | i - view information'](hotkeys for selected line)\n\n"
    content += '## ID         Project name                           Creation date        \n'
    content += '## ---------------------------------------------------------------------\n'
    for project in projects:
      projectsList[project.id] = project.name
      content += '## [%s] %s %s\n' % (str(project.id).ljust(8,' '), project.name.ljust(38,' '), str(project.created_on.strftime('%A %d. %B %Y')).ljust(21, ' '))

    content += '\n### Total projects: %s\n' % len(projects)
    r.insert(edit, 0, content)
    r.set_read_only(True)

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
      # user empty get() to get default web browser.
      wbrowser = webbrowser.get()
    if issue_id:
      url = settings.get('redmine_url')+"/issues/"+issue_id
      wbrowser.open_new(url)
    else:
      sublime.message_dialog("Open Issue!")

class SubRedGoToUrlCommand(sublime_plugin.TextCommand):
  def run(self,edit,url,external):
    current_os = platform.system()
    settings = sublime.load_settings("SubRed.sublime-settings")
    if current_os == 'Darwin':
      wbrowser = webbrowser.get('macosx')
    elif current_os == 'Windows':
      wbrowser = webbrowser.get('windows-default')
    else:
      wbrowser = webbrowser.get()
    if not external:
      url = '{0}{1}'.format(settings.get('redmine_url').rstrip('/'), url)
    wbrowser.open_new(url)




########################## View Actions ##########################
class RedminePostCommentCommand(sublime_plugin.TextCommand):
  def run(self,edit,text):
    issue_id = self.view.name().replace('Redmine Issue #','')
    redmine = SubRedmine.connect()

    issue = redmine.issue.get(issue_id)
    issue.notes = text
    issue.save()

    sublime.status_message('Comment posted!')
    self.view.run_command( 'redmine_fetcher', {'issue_id': issue.id} )

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
    r.settings().set('sub_list_issues', True)

    content = ">> ['enter - view line issue'](hotkeys)\n\n"
    content += '#Issue ID      Subject\n'
    content += '-------------------------------------------\n'
    for issue in issues:
      content += '#%s   %s\n' % (str(issue.id).ljust(11, ' '), issue.subject)
    content += '-------------------------------------------\n'
    content += 'Total: %s\n' % len(issues)

    r.insert(edit, 0, content)
    r.set_read_only(True)

class RedmineFetchProjectsCommand(sublime_plugin.TextCommand):
  def run(self,edit,project_id,query_id):
    redmine = SubRedmine.connect()
    issues = redmine.issue.filter(project_id=project_id,query_id=query_id)
    self.redmine_view(edit, issues, title="Redmine Query List")

  def redmine_view(self, edit, issues, title):
    r = self.view.window().new_file()
    r.set_name(title)
    r.set_scratch(True)
    r.set_syntax_file('Packages/Markdown/Markdown.tmLanguage')
    r.settings().set('sub_list_issues', True)

    content = ">> ['enter - view line issue'](hotkeys)\n\n"
    content += 'Total: %s\n' % len(issues)
    content += '-------------------------------------------\n'
    for issue in issues:
      content += '#%r\t\t%s\n' % (issue.id,issue.subject)

    r.insert(edit, 0, content)
    r.set_read_only(True)

class RedmineGetQueryForProjectCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    for region in self.view.sel():
      if region.empty():
        # Get the selected text
        project_line = self.view.line(region)
        project_line = self.view.substr(project_line)
        project_id = int(project_line[4:12])
        if project_id > 0 :
          sublime.status_message('Openning query list for project ' + project_line[14:53])
          self.view.run_command( 'sub_red_get_query', {'project_id': project_id} )


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

    r.settings().set('sub_red_issue', True)

    if not hasattr(issue, 'fixed_version'):
      issue.fixed_version = ''
    if not hasattr(issue, 'tracker'):
      issue.tracker = 'Issue'
    if not hasattr(issue, 'done_ratio'):
      issue.done_ratio = 0
    if not hasattr(issue, 'estimated_hours'):
      issue.estimated_hours = ''
    if not hasattr(issue, 'spent_hours'):
      issue.spent_hours = ''
    if not hasattr(issue, 'assigned_to'):
      issue.assigned_to = ''

    content = ">> ['c - post a comment | r - refresh issue | s - change state | g - open in browser'](hotkeys for screen)\n"
    content += '-------------------------------------------\n'
    content += '# %s #%s  - %s\n' % (issue.tracker, issue.id, issue.subject)
    content += '## Project:          %s    Priority:       %s\n' % (str(issue.project).ljust(20, ' ')[0:20], str(issue.priority).ljust(10, ' ')[0:10])
    content += '## Status:           %s    %% Done:         %s\n' % (str(issue.status).ljust(20, ' ')[0:20], str(issue.done_ratio).ljust(10, ' ')[0:10])
    content += '## Assignee:         %s    Target Version: %s\n' % (str(issue.assigned_to).ljust(20, ' ')[0:20], str(issue.fixed_version).ljust(10, ' ')[0:10])
    content += '## Estimated Time:   %s    Spent Time:     %s\n' % (str(issue.estimated_hours).ljust(20, ' ')[0:20], str(issue.spent_hours).ljust(10, ' ')[0:10])
    content += '\n## Description\n'
    content += '[%r](%s)' % (issue.created_on.strftime("%A %d. %B %Y"), issue.author.name)
    content += '\n## |\t\t%s\n\n' % issue.description.replace("\r", "").replace("\n","\n## |\t\t")


    if len (issue.journals) > 0 :
        content += '-------------------------------------------\n'
        content += '## History\n'
        for journal in issue.journals:
          if hasattr(journal, 'notes'):
            if journal.notes != '':
              content += '[%r](%s)\n' % (journal.created_on.strftime('%A %d. %B %Y'), journal.user)
              content += '\t%s\n' % journal.notes.replace('\r', '')
              content += '\n'

    if len (issue.changesets) > 0 :
      content += '-------------------------------------------\n'
      content += '## Associated Revisions\n'
      content += ">> ['enter - open selected revision'](hotkeys for revisions)\n\n"
      for changeset in issue.changesets:
        content += '### Revision r%s [ProjectId:%s] \n[%r](%s)\n' % (changeset['revision'], issue.project.id, changeset['committed_on'], changeset['user']['name'])
        content += '%s\n' % changeset['comments'].replace('\r', '')
        content += '\n'

    if len(issue.attachments) > 0:
      content += '-------------------------------------------\n'
      content += '\n## Attachments\n'
      content += '---'
      for f in issue.attachments:
        content += '\n#\t%r (%s)' % (f.filename,f.content_url)

    r.insert(edit, 0, content)
    r.set_read_only(True)
