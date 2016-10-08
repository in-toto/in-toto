"""
    <name> 
       toto_layout/prompt/step_prompt.py

    <description>
        Contains the prompt functions/dispatcher to handle commands provided
        by a user to edit a step. 

        Check go_to_step_prompt for details on how this dispatcheer works

    <author>
        Santiago Torres-Arias

    <date>
        09/27/2016
""" 
import sys

from prompt_toolkit import prompt
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from toto.designlib.history import history
from toto.designlib.util import TotoCommandCompletions, print_help

PROMPT = "toto-layout/{}->step({})> "


def leave(*args):
    """:
            Leave the Toto layout tool 
    """
    yesorno = prompt("You are editing a step, " 
                     "are you sure you want to leave? [Y/n] ")

    if yesorno.startswith("Y"):
        sys.exit()

def add_material_matchrule(step, args):
    """ (MATCH|CREATE|MODIFY|DELETE) <path> [from=<stepname>] :
            Add a matchrule to this step. the MATCH key requires the "from"
            argument
    """
    # FIXME: we should validate this
    if len(args) <=2:
        print("We can't create a step without a name")
        return False

    step["material_matchrules"].add(" ".join(args))
    return False

def list_material_matchrules(step, args):
    """:
            List the existing material matchrules in this step
    """
    print(step['material_matchrules'])
    return False

def remove_material_matchrule(step, args):
    """ <number>:
            Remove matchrule numbered <number>
    """
    # FIXME: I don't know what is the best way to do this....
    return False

def add_product_matchrule(step, args):
    """ (MATCH|CREATE|MODIFY|DELETE) <path> [from=<stepname>] :
            Add a matchrule to this step's product matchrules. The MATCH key
            requires the "from" argument
    """
    # FIXME: we should validate this
    if len(args) <= 2:
        print("We can't add an inspection without a name")
        return False
    name = args[0]

    step["product_matchrules"].add("".join(args))
    return False

def list_product_matchrules(step, args):
    """: 
            List the product matchrules in this step
    """
    print(step['product_matchrules'])

def remove_product_matchrule(step, args):
    """ <number>:
            Remove the product matchrule numbered <number>
    """
    return False

def set_expected_command(step, args):
    """ <path>:
            Load the pubkey from <path> and add it as a functionary pubkey
    """
    if not args:
        print("We need to have *something* as an expected command :/")
        return False

    step['expected_command'] = "".join(args)
    return False

def add_pubkey(step, args):
    """ <keyid>:
            Add the functionary pubkey with keyid <keyid>, A prefix can be 
            be used instead of the whole keyid (it must be the only matching 
            prefix)
    """
    print("Imagine we also did this...")
    return False

def remove_pubkey(step, args):
    """ <keyid>:
            Remove the functionary pubkey with keyid <keyid>, A prefix can be 
            be used instead of the whole keyid (it must be the only matching 
            prefix)
    """
    print("Imagine we also did this...")
    return False

def list_pubkeys(step, args):
    """: 
            List the functionary pubkeys that can sign for this step
    """
    print(step['pubkeys'])
    return False

def go_back(step, args):
    """:  
            Finish editing this step and go back
    """
    # here, we verify that we have a proper step, or prompt for force
    return True


# a dictionary with function pointers to the handlers of this class
VALID_COMMANDS = {
        "add_product_matchrule":  add_product_matchrule,
        "list_product_matchrules": list_product_matchrules,
        "remove_product_matchrule": remove_product_matchrule,
        "add_material_matchrule": add_material_matchrule,
        "list_material_matchrules": list_material_matchrules,
        "remove_material_matchrule": remove_material_matchrule,
        "set_expected_command": set_expected_command,
        "add_pubkey": add_pubkey,
        "remove_pubkey": remove_pubkey,
        "list_pubkeys": list_pubkeys,
        "exit": leave,
        "back": go_back,
        "help": print_help,
    }

def go_to_step_prompt(layout, name, edit=False):
    """ 
        <name>
            go_to_step_prompt

        <description>
            This function handles the user queries. It does so by loading the 
            VALID_COMMANDS strucutre above (that contains function pointers),
            pre-sanitizing input and callind the appropriate command handler.

        <return>
            Once go_back is called, a populated step object is returned to the
            caller (tentatively, the layout-handling prompt)

        <side-effects>
            None
    """

    # setup the environment and eye candy 
    thisprompt = PROMPT.format(layout['name'], name)
    completer = TotoCommandCompletions(VALID_COMMANDS.keys(), [])

    # find the step to edit or create
    if edit:
        print("Imagine we loaded a step instance...")
        step = {"_name": name}
    else:
        print("Imagine we created a step instance...")
        step= {"_name": name} 

    # FIXME: we will use the actual classes later
    step['product_matchrules'] = set()
    step['material_matchrules'] = set()
    step['pubkeys'] = None
    step['expected_command'] = None

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


        should_go_back = VALID_COMMANDS[command[0]](step, command[1:])
        if should_go_back:
            break


    return step
