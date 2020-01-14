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

EXCLUDE_ARGS = ["--exclude"]
EXCLUDE_KWARGS = {
  "dest": "exclude_patterns",
  "required": False,
  "metavar": "<pattern>",
  "nargs": "+",
  "help": ("Do not record 'materials/products' that match one of <pattern>."
          " Passed exclude patterns override previously set patterns, using"
          " e.g.: environment variables or RCfiles. See"
          " ARTIFACT_EXCLUDE_PATTERNS documentation for additional info.")
  }

BASE_PATH_ARGS = ["--base-path"]
BASE_PATH_KWARGS = {
  "dest": "base_path",
  "required": False,
  "metavar": "<path>",
  "help": ("Record 'materials/products' relative to <path>. If not set,"
          " current working directory is used as base path.")
  }

LSTRIP_PATHS_ARGS = ["--lstrip-paths"]
LSTRIP_PATHS_KWARGS = {
  "dest": "lstrip_paths",
  "required": False,
  "nargs": "+",
  "metavar": "<path>",
  "help": ("Record the path of artifacts in link metadata after left"
          " stripping the specified <path> from the full path. If"
          " there are multiple prefixes specified, only a single "
           "prefix can match the path of any artifact and that is "
           "then left stripped. All prefixes are checked to ensure none "
           "of them are a left substring of another.")
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
    title_order = ["Required Named Arguments", "Optional Arguments",
        "Positional Arguments"]

  action_group_dict = {}
  for action_group in parser._action_groups: # pylint: disable=protected-access
    action_group_dict[action_group.title] = action_group

  ordered_action_groups = []
  for title in title_order:
    ordered_action_groups.append(action_group_dict[title])

  parser._action_groups = ordered_action_groups # pylint: disable=protected-access
