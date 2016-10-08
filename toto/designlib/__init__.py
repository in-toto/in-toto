#!/usr/bin/env python
"""
    <name>
        designlib

    <description>
        The toto layout tool "main" handler. It will process the initial
        commands to start a layout-session. Mostly, this will just receive
        "load_layout" to load a layout file, or create_layout, to create it

        Upon receiving a command, a function pointer will be called. Upon
        loading or creating a layout, the layout prompt will be executed in
        turn.

    <parameters>
        executable does not take any command line arguments

    <author>
        Santiago Torres-Arias

    <date>
        09/27/2016
"""
import sys

from prompt_toolkit import prompt as promptk
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.contrib.completers import WordCompleter

from toto.designlib.history import history
from toto.designlib.prompt import go_to_layout_prompt
from toto.designlib.util import TotoCommandCompletions, print_help

PROMPT = "toto-layout> "


def leave(args):
    """:
            Leave the Toto layout tool
    """

    sys.exit()

def create_layout(args):
    """ <name>:
            create a new layout with name <name>
    """
    if len(args) < 1:
        print("You have to supply a layout name!")
        return

    go_to_layout_prompt(name=args[0], load=False)

def load_layout(args):
    """ <filepath>:
            Load a root.layout file from the filesystem
    """
    if len(args) < 1:
        print("You have to supply a path to the root.layout file!")
        return

    go_to_layout_prompt(name=args[0], load=True)

VALID_COMMANDS = {
        "load_layout": load_layout,
        "create_layout": create_layout,
        "exit": leave,
        "help": print_help
        }

def toto_prompt():

    completer = TotoCommandCompletions(VALID_COMMANDS.keys(), None, [])

    while True:

        thisprompt = unicode(PROMPT)
        text = promptk(thisprompt, history=history,
                     auto_suggest=AutoSuggestFromHistory(),
                     completer=completer)

        command = text.split()
        if command[0] in VALID_COMMANDS:

            # if the command is asking for help...
            if command[0] == "help":
                print_help(VALID_COMMANDS)

            # else, dispatch to the generic handlers
            else:
                VALID_COMMANDS[command[0]](command[1:])
        else:
            print("You've input a wrong command")
