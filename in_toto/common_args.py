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
