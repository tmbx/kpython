# -*- mode: python; tab-width: 4; indent-tabs-mode: t; py-indent-offset: 4 -*-

import readline, re
from kbase import PropStore
from kout import *

# Something happened inside the command code.
class CommandException(Exception):
	def __init__(self, message, source):
		Exception.__init__(self, message)
		self.source = source

# Command arguments are incomplete or too numerous.
class CommandArgumentError(Exception):
	"""Thrown by CommandInterpreter.run_command when the demanded
	command doesn't exists."""
	pass

# Command string is invalid.
class CommandParseError(Exception):
	"""Thrown by CommandInterpreter.run_command when the demanded
	command doesn't exists."""
	pass

class CommandError(Exception):
	"""Thrown by CommandInterpreter.run_command when the demanded
	command doesn't exists."""
	pass

class Command:
	"""Empty class.  Just used to identify classes that are commands.
	Should eventually be replace by something else if it's not used."""
	pass

# This is a special command needing access to the list of all
# commands, so it can't be an individual command.
class HelpCommand(Command):
	Name = "help"
	MinParams = 0
	MaxParams = 0
	Syntax = ""
	Help = "List all commands, their syntax, and their descriptions."

	def __init__(self):
		self.max_name_len = None
		self.max_help_len = None		
	
	def run(self, interpreter, cmdname = None):
		if not self.max_name_len:
			self.max_name_len = max([len(c.Name) for c in interpreter.commands])
			self.max_help_len = max([len(c.Help) for c in interpreter.commands]) 

		for cmd in interpreter.commands:
			if cmdname:
				if cmd.Name == cmdname:
					if len(cmd.Syntax) > 0:
						sys.stdout.write(cmd.Name + " " + cmd.Syntax + "\n")
					else:
						sys.stdout.write(cmd.Name + "\n")
					print "  " + cmd.Help					
			else:
				s = cmd.Name.ljust(self.max_name_len, " ")
				s = s + " " + cmd.Help.ljust(self.max_help_len, " ") + "\n"
				out_raw(s)

class CommandCompleter:
	def __init__(self, commands):
		self.words = [c.Name for c in commands]
		self.prefix = None

	def complete(self, prefix, index):
		if prefix != self.prefix:
			self.matching_words = [ w for w in self.words if w.startswith(prefix) ]
			self.prefix = prefix
		try:
			return self.matching_words[index]
		except IndexError:
			return None
    
class CommandInterpreter:
	def _check_commands(self, cmds):
		"""Check the sanity of the command object instances we will use."""
		missing = None
		for cmd in cmds:
			for els in ['Name', 'Syntax', 'Help', 'MaxParams', 'MinParams']:
				if not els in cmd.__class__.__dict__:
					missing = els
					break			
			if missing:
				v = (cmd.__class__, missing)
				raise CommandError("Command class %s is ill-formed.  %s undefined." % v)

			if cmd.MinParams is None:
				raise CommandError("MinParams must be defined for class %s." % cmd.__class__)
				
			if cmd.MaxParams and cmd.MinParams > cmd.MaxParams:
				raise CommandError("MaxParams < MinParams for class %s." % cmd.__class__)
	
    def __init__(self, commands, prompt = "> ", debug_mode = False):		
		self._check_commands(commands)

        self.prompt = prompt
        self.commands = commands + [HelpCommand()]

		self.state = PropStore()
		
		self.do_quit = False
		self.debug = debug_mode

		readline.parse_and_bind("tab: complete")
		readline.set_completer(CommandCompleter(commands).complete)
	
	def run_command(self, cmd_line):
		if not cmd_line or cmd_line == "":
			raise CommandParseError("Empty command.")
		
		cmd_name = cmd_line.pop(0)			

		# Find the command in the command list.
		cmd = self.getCommand(cmd_name)
		if not cmd:
			raise CommandError("The command %s does not exist." % cmd_name)

		args_failed = False
		
		if cmd.MaxParams and len(cmd_line) > cmd.MaxParams:
			args_failed = True

		if len(cmd_line) < cmd.MinParams:
			args_failed = True
				
		if args_failed:
			s = ""
			if len(cmd_line) == 0:
				s = "none passed"
			else:
				s = "%d passed" % len(cmd_line)

			if not cmd.MaxParams:
				args = (cmd_name, cmd.MinParams, s)
				raise CommandArgumentError("%s requires a minimum of %s arguments (%s)" % args)
			else:			
				if cmd.MaxParams == cmd.MinParams:
					args = (cmd_name, cmd.MinParams, s)
					raise CommandArgumentError("%s requires %d arguments (%s)" % args)
				else:
					args = (cmd_name, cmd.MinParams, cmd.MaxParams, s)
					raise CommandArgumentError("%s requires %d to %d arguments (%s)" % args)

		try:
				return cmd.run(self, *cmd_line)
		except Exception, ex:
			if self.debug:
				raise
			else:
				raise CommandException(str(ex), ex)

	def parse_line(self, line):
		buf = ""
		res = []

		cur_sep = None
		in_string = False

		for char in line:
			char_is_space = False
			char_is_quote = False
			char_is_sep = False

			p = re.compile(r'\s')
			if p.match(char):
				char_is_space = True

			if char == '"' or char == "'":
				char_is_quote = True

			if char_is_space or char_is_quote:
				char_is_sep = True

			if not in_string:
				if char_is_sep:
					cur_sep = char
					if char_is_space:
						cur_sep = ' '
					if char_is_quote:
						in_string = True
					continue # skip to next char
				in_string = True

			if in_string:
				if str(char) == str(cur_sep):
					res = res + [ buf ]
					cur_sep = None
					buf = ""
					in_string = False
					continue

			buf = buf + char
			if cur_sep == None:
				cur_sep = ' '

		if in_string:
			if cur_sep == ' ':
				res = res + [ buf ]
			else:
				raise CommandParseError("Could not find ending quote.")

		return res

	def getState(self):
		"""Return the property store of the interpreter."""
		return self.state;

	def setCompleter(self, completer):
		"""Change the readline completer."""
		self.completer = completer
		readline.set_completer(completer.complete)

	def getCommand(self, cmd_name):
		"""Return the command by that name."""
		for cmd in self.commands:
			if cmd_name == cmd.Name:
				return cmd

	def quit(self, val):
		"""Tells the command interpreter loop to stop after the current command."""
		self.do_quit = val

	def parseError(self, ex):
		"""Called on CommandParseError in loop()."""
		print str(ex)

	def argumentError(self, ex):
		"""Called on CommandArgumentError in loop()."""
		print str(ex)

	def commandError(self, ex):
		"""Called on CommandError in loop()."""
		print str(ex)

	def commandException(self, ex):
		"""Called on CommandException in loop()."""
		if ex is CommandException:
			print str(ex.source)
		else:
			print str(ex)

	def simple_input(self, prompt, default_ret = None):
		"""Input some data using raw_input but without saving the history."""
		ret = raw_input(prompt)
		if default_ret and len(ret) == 0:
			ret = default_ret
		readline.remove_history_item(0)
		return ret

	def loop(self):
		"""Main interpreter loop.  Will loop until you quit(True)."""
		while not self.do_quit:
			try:
 				cmd_line_str = raw_input(self.prompt)
				cmd_line = self.parse_line(cmd_line_str)
				self.run_command(cmd_line)

			except EOFError:
				self.quit(True)

			except KeyboardInterrupt:
				self.quit(True)

			# Unknown command.
			except CommandError, ex:
				if self.debug:
					raise
				else:
					self.commandError(ex)

			# Cannot make sense of the command's syntax.
			except CommandParseError, ex:
				if self.debug:
					raise
				else:
					self.parseError(ex)

			# Argument count error, too much or too many.
			except CommandArgumentError, ex:
				if self.debug:
					raise
				else:
					self.argumentError(ex)

			# Happens while the command is running.
			except CommandException, ex:
				if self.debug:
					raise
				else:
					self.commandException(ex)


