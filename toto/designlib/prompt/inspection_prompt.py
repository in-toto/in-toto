"""
    <name> 
       toto_layout/prompt/inspection_prompt.py

    <description>
        Contains the prompt functions/dispatcher to handle commands provided
        by a user to edit an inspection. 

        Check go_to_inspection_prompt for details on how this dispatcheer works

    <author>
        Santiago Torres-Arias

    <date>
        09/27/2016
""" 
import sys

from prompt_toolkit import prompt
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from designlib.history import history
from designlib.util import TotoCommandCompletions, print_help

PROMPT = "toto-layout/{}->inspection({})> "

def leave(*args):
    """:
            Leave the Toto layout tool 
    """
    yesorno = prompt("You are editing an inspection, " 
                     "are you sure you want to leave? [Y/n] ")

    if yesorno.startswith("Y"):
        sys.exit()

def add_material_matchrule(inspection, args):
    """ (MATCH|CREATE|MODIFY|DELETE) <path> [from=<inspectionname>] :
            Add a matchrule to this inspection. the MATCH key requires the "from"
            argument
    """
    # FIXME: we should validate this
    if len(args) <=2:
        print("We can't create a inspection without a name")
        return

    inspection["material_matchrules"].add(" ".join(args))
    return False

def list_material_matchrules(inspection, args):
    """:
            List the existing material matchrules in this inspection
    """
    print(inspection['material_matchrules'])
    return False

def remove_material_matchrule(inspection, args):
    """ <number>:
            Remove matchrule numbered <number>
    """
    # FIXME: I don't know what is the best way to do this....
    return False

def add_product_matchrule(inspection, args):
    """ (MATCH|CREATE|MODIFY|DELETE) <path> [from=<inspectionname>] :
            Add a matchrule to this inspection's product matchrules. The MATCH key
            requires the "from" argument
    """
    # FIXME: we should validate this
    if len(args) <= 2:
        print("We can't add an inspection without a name")
        return
    name = args[0]

    inspection["product_matchrules"].add("".join(args))
    return False

def list_product_matchrules(inspection, args):
    """: 
            List the inspections in the currently-loaded layout
    """
    print(inspection['product_matchrules'])
    return False

def remove_product_matchrule(inspection, args):
    """ <number>:
            Remove the product matchrule numbered <number>
    """
    return False

def set_run(inspection, args):
    """ <command>:
            Set the command to run for this inspection
    """
    if not args:
        print("We need to have *something* as a command :/")
        return False

    inspection['run'] = "".join(args)
    return False

def go_back(step, args):
    """:  
            Discard finish with this inspection and go back
    """
    # FIXME: here we make sure we can actually go back and prompt for discard
    return True


VALID_COMMANDS = {
        "add_product_matchrule":  add_product_matchrule,
        "list_product_matchrules": list_product_matchrules,
        "remove_product_matchrule": remove_product_matchrule,
        "add_material_matchrule": add_material_matchrule,
        "list_material_matchrules": list_material_matchrules,
        "remove_material_matchrule": remove_material_matchrule,
        "set_run": set_run,
        "exit": leave,
        "back": go_back,
        "help": print_help,
    }

def go_to_inspection_prompt(layout, name, edit=False):
    """ 
        <name>
            go_to_inspection_prompt

        <description>
            This function handles the user queries. It does so by loading the 
            VALID_COMMANDS strucutre above (that contains function pointers),
            pre-sanitizing input and callind the appropriate command handler.

        <return>
            Once go_back is called, a populated inspection object is returned
            to the caller (tentatively, the layout-handling prompt)

        <side-effects>
            None
    """

    # setup the environment and eye candy 
    thisprompt = PROMPT.format(layout['name'], name)
    completer = TotoCommandCompletions(VALID_COMMANDS.keys(), [])

    # find the inspection to edit or create
    if edit:
        print("Imagine we loaded an inspection instance...")
        inspection = {"_name": name}
    else:
        print("Imagine we created a inspection instance...")
        inspection= {"_name": name} 

    # FIXME: we will use the actual classes later
    inspection['product_matchrules'] = set()
    inspection['material_matchrules'] = set()
    inspection['run'] = None

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

        should_go_back = VALID_COMMANDS[command[0]](inspection, command[1:])
        if should_go_back:
            break

    return inspection
