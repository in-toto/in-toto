#!/usr/bin/env python
"""
    <name> 
       toto_layout/prompt/layout_prompt.py

    <description>
        Contains the prompt functions/dispatcher to handle commands provided
        by a user to edit a layout. If steps or inspections are to be modified
        the appropriate handler will be called. These handlers also exist in
        prompts.

        see go_to_layout_prompt for more deatils on how this module works.

    <author>
        Santiago Torres-Arias

    <date>
        09/27/2016
""" 
import sys

from prompt_toolkit import prompt
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from designlib.history import history
from designlib.prompt import go_to_step_prompt, go_to_inspection_prompt
from designlib.util import TotoCommandCompletions, print_help

PROMPT = "toto-layout/{}> "

def dummy_command(*args):
    """: *** dummy wrapper for the commands that are not yet implemented *** """
    print("called!")
    pass

def leave(*args):
    """:
            Leave the Toto layout tool 
    """
    yesorno = prompt("You are editing a layout, " 
                     "are you sure you want to leave? [Y/n] ")

    if yesorno.startswith("Y"):
        sys.exit()


def add_step(layout, args):
    """ <name>:
            Add a step to the currently-loaded layout
    """
    if len(args) < 1:
        print("We can't create a step without a name")
        return

    name = args[0]

    if name in layout['steps'] or name in layout['inspections']:
        print("You can't add a step with that name. Remove the step or "
              "validation with that name, or use edit_step instead")
        return

    layout['steps'].add(go_to_step_prompt(layout, name, edit=False))

def list_steps(layout, args):
    """:
            List the existing steps in the currently-loaded layout
    """
    print(layout['steps'])

def remove_step(layout, args):
    """ <name>:
            Remove the step <name> from the currently-loaded layout
    """
    if len(args) < 1:
        print("We can't remove a step without a name")
        return
    name = args[0]

    if name not in layout['steps']:
        print("Cannot remove non-existing layout step")
        return

    del layout['steps'][name]


def add_inspection(layout, args):
    """ <name>:
            Add an inspection <name> to the currently-loaded layout
    """
    if len(args) < 1:
        print("We can't add an inspection without a name")
        return
    name = args[0]

    if name in layout['steps'] or name in layout['inspections']:
        print("You can't add an inspection with that name. Remove the step or "
              "validation with that name, or use edit_validation instead")
        return

    go_to_inspection_prompt(layout, name, edit=False)


def list_inspections(layout, args):
    """: 
            List the inspections in the currently-loaded layout
    """
    print(layout['inspections'])

def remove_inspection(layout, args):
    """ <name>:
            Remove the inspection <name> from the currenlty-loaded layout
    """
    if len(args) < 1:
        print("We can't add an inspection without a name")
        return
    name = args[0]

    if name not in layout['inspections']:
        print("Cannot remove non-existing layout inspection")
        return

    del layout['inspections'][name]

def add_functionary_pubkey(layout,args):
    """ <path>:
            Load the pubkey from <path> and add it as a functionary pubkey
    """
    print("Imagine we did this...")

def remove_functionary_pubkey(layout, args):
    """ <keyid>:
            Remove the functionary pubkey with keyid <keyid>, A prefix can be 
            be used instead of the whole keyid (it must be the only matching 
            prefix)
    """
    print("Imagine we also did this...")

def list_functionary_pubkeys(layout, args):
    """: 
            List the functionary pubkeys in the currently-loaded layout
    """
    print(layout['functionary_pubkeys'])

def sign_and_save_layout(layout, args):
    """ [filename]:
            Sign the current layout and save it to disk. If no filename is 
            specified, "root.layout" will be used
    """
    print("imagine we did this...")

def go_back(args):
    """:  
            Discard this layout and go back
    """
    pass


VALID_COMMANDS = {
        "add_step":  add_step,
        "list_steps": list_steps,
        "remove_step": remove_step,
        "add_inspection": add_inspection,
        "list_inspections": list_inspections,
        "remove_inspection": remove_inspection,
        "add_functionary_pubkey": add_functionary_pubkey,
        "remove_functionary_pubkey": remove_functionary_pubkey,
        "list_functionary_pubkeys": list_functionary_pubkeys,
        "sign_and_save_layout": sign_and_save_layout,
        "exit": leave,
        "back": go_back,
        "help": print_help,
    }

def go_to_layout_prompt(name, load):
    """ 
        <name>
            go_to_layout_prompt

        <description>
            This function handles the user queries regarding layouts. It does
            so by loading the VALID_COMMANDS strucutre above (that contains
            function pointers), pre-sanitizing input and callind the
            appropriate command handler.

        <return>
            Once go_back is called, a populated layout object is returned to
            the caller (tentatively, the main handling prompt). Do notice
            that sign_and_save_layout is necessary to save the layout in this
            context.

        <side-effects>
            If sign_and_save_layout is called, a file called [name].layout
            will be created.
    """


    # setup the environment and eye candy 
    thisprompt = PROMPT.format(name)
    completer = TotoCommandCompletions(VALID_COMMANDS.keys(), [])

    # actually load the layout
    if load:
        print("Imagine we loaded a layout instance...")
        layout = {"name": name}
    else:
        print("Imagine we created a layout instance...")
        layout = {"name": name} 

    # FIXME: we will use the actual classes later
    layout['steps'] = set()
    layout['inspections'] = set()
    layout['functionary_pubkeys'] = set()
    layout['expiration'] = None

    while True:

        text = prompt(thisprompt, history=history, 
                     auto_suggest=AutoSuggestFromHistory(),
                     completer=completer)

        command = text.split()

        if command[0] not in VALID_COMMANDS:
            print("You've input a wrong command")
            continue

        # do generic dispatching
        if command[0] == "help":
            print_help(VALID_COMMANDS)
            continue

            break

        else:
            VALID_COMMANDS[command[0]](layout, command[1:])

    return layout
