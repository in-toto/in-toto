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

from toto.designlib.history import history
from toto.designlib.prompt import go_to_step_prompt, go_to_inspection_prompt
from toto.designlib.util import (TotoCommandCompletions, print_help, 
                                prompt_password)

from toto.models.layout import Layout

from toto.ssl_crypto.keys import (format_rsakey_from_pem,
                                  import_rsakey_from_encrypted_pem)
from toto.ssl_commons.exceptions import FormatError

PROMPT = unicode("toto-layout/{}> ")

def leave(*args):
    """:
            Leave the Toto layout tool 
    """
    message = unicode("You are editing a layout, are you sure you "
                      "want to leave? [Y/n] ")
    yesorno = prompt(message)

    if yesorno.startswith("Y"):
        sys.exit()

def edit_step(state, layout, args):
    """ <name>:
            Edit a step with the name <name> in the currently loaded layout
    """
    if len(args) < 1:
        print("We can't edit a step without a name!")
        return

    name = args[0]
    go_to_step_prompt(layout, name, edit=True)

def add_step(state, layout, args):
    """ <name>:
            Add a step to the currently-loaded layout
    """
    if len(args) < 1:
        print("We can't create a step without a name")
        return

    name = args[0]

    if name in layout.steps or name in layout.inspect:
        print("You can't add a step with that name. Remove the step or "
              "validation with that name, or use edit_step instead")
        return

    layout.steps.append(go_to_step_prompt(layout, name, edit=False))

def list_steps(state, layout, args):
    """:
            List the existing steps in the currently-loaded layout
    """
    print("{}".format(layout.steps))

def remove_step(state, layout, args):
    """ <name>:
            Remove the step <name> from the currently-loaded layout
    """
    if len(args) < 1:
        print("We can't remove a step without a name")
        return
    name = args[0]

    if name not in layout.steps:
        print("Cannot remove non-existing layout step")
        return

    # FIXME: how do we delete a step.
    # del layout.steps.name


def add_inspection(state, layout, args):
    """ <name>:
            Add an inspection <name> to the currently-loaded layout
    """
    if len(args) < 1:
        print("We can't add an inspection without a name")
        return
    name = args[0]

    if name in layout.steps or name in layout.inspections:
        print("You can't add an inspection with that name. Remove the step or "
              "validation with that name, or use edit_validation instead")
        return

    go_to_inspection_prompt(layout, name, edit=False)


def list_inspections(state, layout, args):
    """: 
            List the inspections in the currently-loaded layout
    """
    print(layout.inspections)

def remove_inspection(state, layout, args):
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

    # FIXME: how ?
    # del layout['inspections'][name]

def add_functionary_pubkey(state, layout, args):
    """ <path>:
            Load the pubkey from <path> and add it as a functionary pubkey
    """
    if len(args) < 1:
        print("I require a filepath to load!")
        return

    filepath = args[0]
    # Read the contents of 'filepath' that should be an encrypted PEM.
    try:
        with open(filepath, 'rb') as fp:
            pem = fp.read().decode('utf-8')

    except IOError as e:
        print("Could not load key {}".format(e))
        return

    try:
        rsa_key = format_rsakey_from_pem(pem)

    except FormatError as e:
        raise Exception("Could not load RSA key "
                        "from file {}".format(filepath))

    # FIXME: should check if the key already exists in the list...
    layout.keys.append(rsa_key)

def remove_functionary_pubkey(state, layout, args):
    """ <keyid>:
            Remove the functionary pubkey with keyid <keyid>, A prefix can be 
            be used instead of the whole keyid (it must be the only matching 
            prefix)
    """
    if len(args) < 1:
        print("We require the keyid you want to remove from this layout")
        return

    keyid = args[0]

    for key in layout.keys:
        if key['keyid'] == keyid:
            layout.keys.remove(key)
            break
    else:
        print("Couldn't find the key!")

    print("Successfuly removed key")


def list_functionary_pubkeys(state, layout, args):
    """: 
            List the functionary pubkeys in the currently-loaded layout
    """
    i = 1
    for key in layout.keys:
        print("[{}]({}) {}".format(i, key['keytype'], key['keyid']))


def load_project_owner_signing_key(state, layout, args):
    """ <path>:
            Load the project owner private to sign this layout
    """

    if len(args) < 1:
        print("We need a filepath to load the key!")
        return

    filepath = args[0]
    message = unicode('Enter a password for the encrypted RSA file: ')
    password = prompt_password(message)

    with open(filepath, 'rb') as file_object:
        encrypted_pem = file_object.read().decode('utf-8')

    rsa_key = import_rsakey_from_encrypted_pem(encrypted_pem, password)

    state.layout_private_key = rsa_key


def sign_and_save_layout(state, layout, args):
    """ [filename]:
            Sign the current layout and save it to disk. If no filename is 
            specified, "root.layout" will be used
    """
    if not state.layout_private_key:
        print("I can't save this state without the private key!")
        return

    layout.sign(state.layout_private_key)
    layout.dump(state.layout_filename)


def go_back(state, layout, args):
    """:  
            Discard this layout and go back
    """
    pass


class promptState(object):
    """ This class holds state information about the context of this prompt """
    layout_private_key = None
    is_layout_dirty = False
    layout_filename = None


VALID_COMMANDS = {
        "add_step":  add_step,
        "edit_step": edit_step,
        "list_steps": list_steps,
        "remove_step": remove_step,
        "add_inspection": add_inspection,
        "list_inspections": list_inspections,
        "remove_inspection": remove_inspection,
        "add_functionary_pubkey": add_functionary_pubkey,
        "remove_functionary_pubkey": remove_functionary_pubkey,
        "list_functionary_pubkeys": list_functionary_pubkeys,
        "sign_and_save_layout": sign_and_save_layout,
        "load_project_owner_signing_key": load_project_owner_signing_key,
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


    # actually load the layout
    state = promptState()
    if load:
        layout = Layout.read_from_file(name)
        state.filename = name
    else:
        layout = Layout()
        state.layout_filename = "{}.layout".format(name)

    # setup the environment and eye candy
    thisprompt = PROMPT.format(name)
    completer = TotoCommandCompletions(VALID_COMMANDS.keys(), layout, [])

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

        else:
            VALID_COMMANDS[command[0]](state, layout, command[1:])

    return layout
