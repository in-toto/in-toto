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
from prompt_toolkit import prompt

import getpass
import os
import glob

def print_help(args):
    """:
            Print this help
    """

    allfuncs = sorted(args.keys())
    fmt="\t{}{}\n"
    text = [fmt.format(i, args[i].__doc__) for i in allfuncs]
    print("Available commands in this context:\n")
    print("".join(text))

def prompt_password(message="Please provide a password:",
                    confirmation = False):

    while True:
        password = prompt(message, is_password=True)
        if confirmation:
            pw_confirmation = prompt("Please repeat: ", is_password=True)
            if pw_confirmation != password:
                print("confirmation doesn't match")
                continue

        break

    return password


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
   
    COMMANDS_THAT_USE_KEYIDS = {"add_pubkey", "remove_pubkey", 
                                "remove_functionary_pubkey"} 
    COMMANDS_THAT_USE_PATHS = {"add_functionary_pubkey", 
                               "load_project_owner_signing_key"}
    COMMANDS_THAT_USE_STEPNAMES = {"edit_step", "edit_inspection",
                                   "remove_step", "remove_inspection"}
    COMMANDS_THAT_USE_MATCHRULES = {"add_material_matchrule",
                                    "add_product_matchrule"}
    commands = None
    args = None
    layout = None

    def __init__(self, commands, layout, args):
        self.commands = commands
        self.args = args
        self.layout = layout

    def get_completions(self, document, complete_event):

        if document.char_before_cursor == ' ':
            return

        args = document.text.split()
        command = args[0]

        lengths = [len(x) for x in args]
        total_length = 0
        parameter_location = 0
        for length in lengths:

            total_length += length

            if total_length >= document.cursor_position:
                wordstart = -length
                parameter_location = lengths.index(length)
                chunk = args[parameter_location]
                break

            total_length += 1

        else:
            wordstart = 0
            chunk = command
        
        completions = []
        if parameter_location == 0:
            completions = self.commands
        else:
            if command in self.COMMANDS_THAT_USE_KEYIDS:
                completions = [x['keyid'] for x in self.layout.keys]
            elif command in self.COMMANDS_THAT_USE_PATHS:
                files_in_folder = os.path.join(".", os.path.dirname(chunk))
                completions = os.listdir(files_in_folder)
                try:
                    wordstart = chunk.rindex(os.sep) - len(chunk) + 1
                except:
                    pass
                chunk = os.path.basename(chunk)

            elif command in self.COMMANDS_THAT_USE_STEPNAMES:
                all_steps = self.layout.steps + self.layout.inspect
                completions = [x.name for x in all_steps]

            elif command in self.COMMANDS_THAT_USE_MATCHRULES:
                completions = self._complete_matchrule(args, 
                                                       parameter_location)

        # figure out if this is a command
        for candidate_completion in completions:
            if candidate_completion.startswith(chunk):
                yield Completion(candidate_completion, wordstart)


    def  _complete_matchrule(self, args, parameter_location):

        KEYWORDS = {"CREATE", "DELETE", "MODIFY", "MATCH"}
        # if parameter location is 2, then we check for keywords
        if parameter_location == 1:
            return KEYWORDS

        elif args[1] == "MATCH":
            if parameter_location == 2:
                return ["MATERIAL" , "PRODUCT"]

            elif parameter_location == 3:
                return []

            elif parameter_location == 4:
                return ["FROM"]

            elif parameter_location == 5:
                return [x.name for x in self.layout.steps]

        return [] 
