"""
    <name> 
       toto_layout/util 

    <description>
        The util functions for Toto_layout contain helpers that are used 
        throughout all modules

    <author>
        Santiago Torres-Arias

    <date>
        09/27/2016
""" 
from prompt_toolkit.completion import Completer, Completion

def print_help(args):
    """:
            Print this help
    """

    allfuncs = sorted(args.keys())
    fmt="\t{}{}\n"
    text = [fmt.format(i, args[i].__doc__) for i in allfuncs]
    print("Available commands in this context:\n")
    print("".join(text))


class TotoCommandCompletions(Completer):
    """ 
        <name> 
            TotoCommandCompletions

        <description>
            Generic completion class for the Toto layout tool it will try to
            figure out which commands are available in the current promp
            context and which arguments a command may recieve.

        <see-more>
            Check out the docs for this class:
            https://python-prompt-toolkit.readthedocs.io/en/stable/pages/reference.html#prompt_toolkit.completion.Completer

    """
    
    commands = None
    args = None

    def __init__(self, commands, args):
        self.commands = commands
        self.args = args

    def get_completions(self, document, complete_event):

        command = document.text.split()

        startpos, endpos =  document.find_boundaries_of_current_word()

        wordstart = startpos
        startpos += document.cursor_position
        endpos += document.cursor_position

        if startpos == 0 and endpos == 0:
            return

        if startpos != 0:
            return

        this_command = document.text[startpos:endpos]

        # figure out if this is a command
        for command in self.commands:
            if command.startswith(this_command):
                yield Completion(command, wordstart)
