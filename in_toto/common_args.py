"""
<Program Name>
  common_args.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Mar 09, 2018

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides a collection of constants that can be used as `*args` or `**kwargs`
  to argparse.ArgumentParser.add_argument() for cli tools with common
  command line arguments.

  Example Usage:

  ```
  form in_toto.common_args import EXCLUDE_ARGS, EXCLUDE_KWARGS
  parser = argparse.ArgumentParser()
  parser.add_argument(*EXCLUDE_KWARGS, **EXCLUDE_KWARGS)
  ```

"""
from in_toto import SUPPORTED_KEY_TYPES, KEY_TYPE_RSA, KEY_TYPE_ED25519

EXCLUDE_ARGS = ["--exclude"]
EXCLUDE_KWARGS = {
  "dest": "exclude_patterns",
  "required": False,
  "metavar": "<pattern>",
  "nargs": "+",
  "help": ("path patterns to match paths that should not be recorded as"
           " 'materials' or 'products'. Passed patterns override patterns"
           " defined in environment variables or config files. See Config docs"
           " for details.")
  }

BASE_PATH_ARGS = ["--base-path"]
BASE_PATH_KWARGS = {
  "dest": "base_path",
  "required": False,
  "metavar": "<path>",
  "help": ("base path for relative paths passed via '--materials' and"
           " '--products'. It is used to locate and record artifacts, and is"
           " not included in the resulting link metadata. Default is the"
           " current working directory.")
  }

LSTRIP_PATHS_ARGS = ["--lstrip-paths"]
LSTRIP_PATHS_KWARGS = {
  "dest": "lstrip_paths",
  "required": False,
  "nargs": "+",
  "metavar": "<path>",
  "help": ("path prefixes used to left-strip artifact paths before storing"
           " them to the resulting link metadata. If multiple prefixes are"
           " specified, only a single prefix can match the path of any"
           " artifact and that is then left-stripped. All prefixes are checked"
           " to ensure none of them are a left substring of another.")
}

KEY_ARGS = ["-k", "--key"]
KEY_KWARGS = {
 "type": str,
 "metavar": "<path>",
 "help": ("path to a private key file to sign the resulting link metadata."
          " The keyid prefix is used as an infix for the link metadata"
          " filename, i.e. '<name>.<keyid prefix>.link'. See '--key-type' for"
          " available formats. Passing one of '--key' or '--gpg' is required.")
}

KEY_TYPE_ARGS = ["-t", "--key-type"]
KEY_TYPE_KWARGS = {
  "dest": "key_type",
  "type": str,
  "choices": SUPPORTED_KEY_TYPES,
  "default": KEY_TYPE_RSA,
  "help": ("type of key specified by the '--key' option. '{rsa}' keys are"
           " expected in a 'PEM' format and '{ed25519}' in a custom"
           " 'securesystemslib/json' format. Default is '{rsa}'.".format(
           rsa=KEY_TYPE_RSA, ed25519=KEY_TYPE_ED25519))
}

KEY_PASSWORD_ARGS = ["-P", "--password"]
KEY_PASSWORD_KWARGS = {
  "nargs": "?",
  "const": True,
  "metavar": "<password>",
  "help": ("password for encrypted key specified with '--key'. Passing  '-P'"
           " without <password> opens a prompt. If no password is passed, or"
           " entered on the prompt, the key is treated as unencrypted. (Do "
           " not confuse with '-p/--products'!)")
}
def parse_password_and_prompt_args(args):
  """Parse -P/--password optional arg (nargs=?, const=True). """
   # --P was provided without argument (True)
  if args.password is True:
    password = None
    prompt = True
  # --P was not provided (None), or provided with argument (<password>)
  else:
    password = args.password
    prompt = False

  return password, prompt

GPG_ARGS = ["-g", "--gpg"]
GPG_KWARGS = {
  "nargs": "?",
  "const": True,
  "metavar": "<id>",
  "help": ("GPG keyid to sign the resulting link metadata.  When '--gpg' is"
           " passed without the keyid, the default GPG key is used. The keyid"
           " prefix is used as an infix for the link metadata filename, i.e."
           " '<name>.<keyid prefix>.link'. Passing one of '--key' or '--gpg'"
           " is required.")
}

GPG_HOME_ARGS = ["--gpg-home"]
GPG_HOME_KWARGS = {
  "dest": "gpg_home",
  "type": str,
  "metavar": "<path>",
  "help": ("path to a GPG home directory used to load a GPG key identified"
           " by '--gpg'. If '--gpg-home' is not passed, the default GPG home"
           " directory is used.")
}

VERBOSE_ARGS = ["-v", "--verbose"]
VERBOSE_KWARGS = {
  "dest": "verbose",
  "action": "store_true",
  "help": "show more output"
}

QUIET_ARGS = ["-q", "--quiet"]
QUIET_KWARGS = {
  "dest": "quiet",
  "action": "store_true",
  "help": "suppress all output"
}

METADATA_DIRECTORY_ARGS = ["-d", "--metadata-directory"]
METADATA_DIRECTORY_KWARGS = {
  "required": False,
  "type": str,
  "metavar": "<directory>",
  "help": ("path to a directory to dump metadata. If '--metadata-directory'"
           " is not passed, the current working direcotry is used.")
}


def title_case_action_groups(parser):
  """Capitalize the first character of all words in the title of each action
  group of the passed parser.

  This is useful for consistency when using the sphinx argparse extension,
  which title-cases default action groups only.

  """
  for action_group in parser._action_groups: # pylint: disable=protected-access
    action_group.title = action_group.title.title()


def sort_action_groups(parser, title_order=None):
  """Sort action groups of passed parser by their titles according to the
  passed (or a default) order.

  """
  if title_order is None:
    title_order = ["Required Named Arguments", "Positional Arguments",
        "Optional Arguments"]

  action_group_dict = {}
  for action_group in parser._action_groups: # pylint: disable=protected-access
    action_group_dict[action_group.title] = action_group

  ordered_action_groups = []
  for title in title_order:
    ordered_action_groups.append(action_group_dict[title])

  parser._action_groups = ordered_action_groups # pylint: disable=protected-access
