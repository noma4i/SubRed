import sublime, sublime_plugin, os, sys, imp

__path__ = os.path.dirname(__file__)
libs_path = os.path.join(__path__, 'libs')

import redmine

class RedClient(object):
  def __init__(self, window):
    sublime.active_window().create_output_panel("scope")
    result_page = window.new_file()
    result_page.set(title ,"d")
    print(dir(result_page))

  def dump(obj):
    for attr in dir(obj):
      print (attr, getattr(obj, attr))
class SubRedCommand(sublime_plugin.TextCommand):
  def run(self, edit, text):
    self.view.replace(edit, sublime.Region(0, self.view.size()), text)
