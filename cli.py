#-----------------------------------------------------------------------------
"""
Command Line Interface

Implements a CLI with:

* hierarchical menus
* command tab completion
* command history
* context sensitive help
* command editing

Notes:

Menu Tuple Format:
  (name, submenu, description) - submenu
  (name, leaf) - leaf command with generic <cr> help
  (name, leaf, help) - leaf command with specific argument help

Help Format:
  (parm, descr)

Leaf Functions:

def leaf_function(ui, args):
 .....

ui: the ui object passed by the application to cli()
args: the argument list from the command line

The general help for a leaf function is the docstring for that function.
"""
#-----------------------------------------------------------------------------

import linenoise
import util

#-----------------------------------------------------------------------------
# common help for cli leaf functions

cr_help = (
  ('<cr>', 'perform the function'),
)

general_help = (
  ('?', 'display command help - Eg. ?, show ?, s?'),
  ('<up>', 'go backwards in command history'),
  ('<dn>', 'go forwards in command history'),
  ('<tab>', 'auto complete commands'),
  ('* note', 'commands can be incomplete - Eg. sh = sho = show'),
)

history_help = (
  ('<cr>', 'display all history'),
  ('<index>', 'recall history entry <index>'),
)

#-----------------------------------------------------------------------------

def split_index(s):
  """split a string on whitespace and return the substring indices"""
  # start and end with whitespace
  ws = True
  s += ' '
  start = []
  end = []
  for (i, c) in enumerate(s):
    if not ws and c == ' ':
      # non-whitespace to whitespace
      end.append(i)
      ws = True
    elif ws and c != ' ':
      # whitespace to non-whitespace
      start.append(i)
      ws = False
  return zip(start, end)

#-----------------------------------------------------------------------------

class cli(object):
  """command line interface"""

  def __init__(self, ui, history=None):
    self.ui = ui
    self.ln = linenoise.linenoise()
    self.ln.set_completion_callback(self.completion_callback)
    self.ln.set_hotkey('?')
    self.ln.history_load(history)
    self.poll = None
    self.root = None
    self.prompt = '> '
    self.running = True

  def set_root(self, root):
    """set the menu root"""
    self.root = root

  def set_prompt(self, prompt):
    """set the command prompt"""
    self.prompt = prompt

  def set_poll(self, poll):
    """set the external polling function"""
    self.poll = poll

  def display_error(self, msg, cmds, idx):
    """display a parse error string"""
    marker = []
    for (i, cmd) in enumerate(cmds):
      l = len(cmd)
      if i == idx:
        marker.append('^' * l)
      else:
        marker.append(' ' * l)
    s = '\n'.join([msg, ' '.join(cmds), ' '.join(marker)])
    self.ui.put('%s\n' % s)

  def display_function_help(self, help_info):
    """display function help"""
    s = []
    for (parm, descr) in help_info:
      p_str = (parm, '')[parm is None]
      d_fmt = (': %s', '  %s')[parm is None]
      d_str = (d_fmt % descr, '')[descr is None]
      s.append(['  ', p_str, d_str])
    self.ui.put('%s\n' % util.display_cols(s, [0, 16, 0]))

  def command_help(self, cmd, menu):
    """display help results for a command at a menu level"""
    s = []
    for item in menu:
      name = item[0]
      if name.startswith(cmd):
        if isinstance(item[1], tuple):
          # submenu: the next string is the help
          descr = item[2]
        else:
          # command: docstring is the help
          descr = item[1].__doc__
        s.append(['  ', name, ': %s' % descr])
    self.ui.put('%s\n' % util.display_cols(s, [0, 16, 0]))

  def function_help(self, item):
    """display help for a leaf function"""
    if len(item) > 2:
      help_info = item[2]
    else:
      help_info = cr_help
    self.display_function_help(help_info)

  def general_help(self):
    """display general help"""
    self.display_function_help(general_help)

  def display_history(self, args):
    """display the command history"""
    # get the history
    h = self.ln.history_list()
    n = len(h)
    if len(args) == 1:
      # retrieve a specific history entry
      idx = util.int_arg(self.ui, args[0], (0, n - 1), 10)
      if idx is None:
        return
      # Return the next line buffer.
      # Note: linenoise wants to add the line buffer as the zero-th history entry.
      # It can only do this if it's unique- and this isn't because it's a prior
      # history entry. Make it unique by adding a trailing whitespace. The other
      # entries have been stripped prior to being added to history.
      return h[n - idx - 1] + ' '
    else:
      # display all history
      if n:
        s = ['%-3d: %s' % (n - i - 1, l) for (i, l) in enumerate(h)]
        self.ui.put('%s\n' % '\n'.join(s))
      else:
        self.ui.put('no history\n')
      return ''

  @staticmethod
  def completions(line, minlen, cmd, names):
    """return the list of line completions"""
    line += ('', ' ')[cmd == '' and line != '']
    lines = ['%s%s' % (line, x[len(cmd):]) for x in names]
    # pad the lines to a minimum length, we don't want
    # the cursor to move about unecessarily
    return [l + ' ' * max(0, minlen - len(l)) for l in lines]

  def completion_callback(self, cmd_line):
    """return a tuple of line completions for the command line"""
    line = ''
    # split the command line into a list of command indices
    cmd_list = split_index(cmd_line)
    # trace each command through the menu tree
    menu = self.root
    for (start, end) in cmd_list:
      cmd = cmd_line[start:end]
      line = cmd_line[:end]
      # How many items does this token match at this level of the menu?
      matches = [x for x in menu if x[0].startswith(cmd)]
      if len(matches) == 0:
        # no matches, no completions
        return None
      elif len(matches) == 1:
        item = matches[0]
        if len(cmd) < len(item[0]):
          # it's an unambiguous single match, but we still complete it
          return self.completions(line, len(cmd_line), cmd, [item[0],])
        else:
          # we have the whole command - is this a submenu or leaf?
          if isinstance(item[1], tuple):
            # submenu: switch to the submenu and continue parsing
            menu = item[1]
            continue
          else:
            # leaf function: no completions to offer
            return None
      else:
        # Multiple matches at this level. Return the matches.
        return self.completions(line, len(cmd_line), cmd, [x[0] for x in matches])
    # We've made it here without returning a completion list.
    # The prior set of tokens have all matched single submenu items.
    # The completions are all of the items at the current menu level.
    return self.completions(line, len(cmd_line), '', [x[0] for x in menu])

  def parse_cmdline(self, line):
    """
    parse and process the current command line
    return a string for the new command line.
    This is generally '' (empty), but may be non-empty
    if the user needs to edit a pre-entered command.
    """
    # scan the command line into a list of tokens
    cmd_list = [x for x in line.split(' ') if x != '']
    # if there are no commands, print a new empty prompt
    if len(cmd_list) == 0:
      return ''
    # trace each command through the menu tree
    menu = self.root
    for (idx, cmd) in enumerate(cmd_list):
      # A trailing '?' means the user wants help for this command
      if cmd[-1] == '?':
        # strip off the '?'
        cmd = cmd[:-1]
        self.command_help(cmd, menu)
        # strip off the '?' and recycle the command
        return line[:-1]
      # try to match the cmd with a unique menu item
      matches = []
      for item in menu:
        if item[0] == cmd:
          # accept an exact match
          matches = [item]
          break
        if item[0].startswith(cmd):
          matches.append(item)
      if len(matches) == 0:
        # no matches - unknown command
        self.display_error('unknown command', cmd_list, idx)
        # add it to history in case the user wants to edit this junk
        self.ln.history_add(line.strip())
        # go back to an empty prompt
        return ''
      if len(matches) == 1:
        # one match - submenu/leaf
        item = matches[0]
        if isinstance(item[1], tuple):
          # this is a submenu
          # switch to the submenu and continue parsing
          menu = item[1]
          continue
        else:
          # this is a leaf function - get the arguments
          args = cmd_list[idx:]
          del args[0]
          if len(args) != 0:
            if args[-1][-1] == '?':
              self.function_help(item)
              # strip off the '?', repeat the command
              return line[:-1]
          # call the leaf function
          rc = item[1](self.ui, args)
          # post leaf function actions
          if rc is not None:
            # currently only history retrieval returns not None
            # the return code is the next line buffer
            return rc
          else:
            # add the command to history
            self.ln.history_add(line.strip())
            # return to an empty line
            return ''
      else:
        # multiple matches - ambiguous command
        self.display_error('ambiguous command', cmd_list, idx)
        return ''
    # reached the end of the command list with no errors and no leaf function.
    self.ui.put('additional input needed\n')
    return line

  def run(self):
    """get and process cli commands in a loop"""
    line = ''
    while self.running:
      line = self.ln.read(self.prompt, line)
      if line is not None:
        line = self.parse_cmdline(line)
      else:
        # exit: ctrl-C/ctrl-D
        self.running = False
    self.ln.history_save('history.txt')

  def exit(self):
    """exit the cli"""
    self.running = False

#-----------------------------------------------------------------------------
