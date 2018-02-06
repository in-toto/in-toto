#!/usr/bin/env python
"""
<Program Name>
  in_toto_run.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  June 27, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides a command line interface which takes any link command of the software
  supply chain as input and wraps in_toto metadata recording.

  in_toto run options are separated from the command to be executed by
  a double dash.

  The implementation of the tasks can be found in runlib.

  Example Usage
  ```
  in-toto-run --step-name write-code --materials . --products . --key bob \
      -- vi foo.py
  ```

<Arguments>
  step_name:
          A unique name to relate link metadata with a step defined in the
          layout.
  material_list:
          List of file or directory paths that should be recorded as
          materials.
  product_list:
          List of file or directory paths that should be recorded as
          products.
  link_cmd_args:
          A list where the first element is a command and the remaining
          elements are arguments passed to that command.
  record_streams:
          A bool that specifies whether to redirect standard output and
          and standard error to a temporary file which is returned to the
          caller (True) or not (False).
  signing_key:
          If not None, link metadata is signed with this key.
          Format is securesystemslib.formats.KEY_SCHEMA
  gpg_keyid:
          If not None, link metadata is signed with a gpg key identified
          by the passed keyid.
  gpg_use_default:
          If True, link metadata is signed with default gpg key.
  gpg_home:
          Path to GPG keyring (if not set the default keyring is used).


<Return Codes>
  2 if an exception occurred during argument parsing
  1 if an exception occurred
  0 if no exception occurred

"""

import sys
import argparse
import logging
import in_toto.user_settings
from in_toto import (util, runlib)


# Command line interfaces should use in_toto base logger (c.f. in_toto.log)
log = logging.getLogger("in_toto")


def main():
  """Parse arguments, load key from disk (prompts for password if key is
  encrypted) and call in_toto_run. """

  parser = argparse.ArgumentParser(
      description="Executes link command and records metadata")

  parser.usage = ("%(prog)s <named arguments> [optional arguments]"
      " -- <command> [args]")

  named_args = parser.add_argument_group("required named arguments")

  # FIXME: Do we limit the allowed characters for the name?
  named_args.add_argument("-n", "--step-name", type=str, required=True,
      help="Unique name for link metadata", metavar="<unique step name>")

  parser.add_argument("-m", "--materials", type=str, required=False,
      nargs='+', help="Files to record before link command execution",
      metavar="<material path>")

  parser.add_argument("-p", "--products", type=str, required=False,
      nargs='+', help="Files to record after link command execution",
      metavar="<product path>")

  named_args.add_argument("-k", "--key", type=str,
      help="Path to private key to sign link metadata (PEM)",
      metavar="<signing key path>")

  named_args.add_argument("-g", "--gpg", nargs="?", const=True,
      metavar="<gpg keyid>", help=("GPG keyid to sign link metadata "
      "(if set without argument, the default key is used)"))

  parser.add_argument("--gpg-home", dest="gpg_home", type=str,
      help="Path to GPG keyring (if not set the default keyring is used)",
      metavar="<gpg keyring path>")

  parser.add_argument("-b", "--record-streams",
      help="If set redirects stdout/stderr and stores to link metadata",
      dest="record_streams", default=False, action="store_true")

  parser.add_argument("-x", "--no-command",
      help="Set if step does not have a command",
      dest="no_command", default=False, action="store_true")

  verbosity_args = parser.add_mutually_exclusive_group(required=False)
  verbosity_args.add_argument("-v", "--verbose", dest="verbose",
      help="Verbose execution.", action="store_true")

  verbosity_args.add_argument("-q", "--quiet", dest="quiet",
      help="Suppress all output.", action="store_true")


  # FIXME: This is not yet ideal.
  # What should we do with tokens like > or ; ?
  parser.add_argument("link_cmd", nargs="*", metavar="<command>",
    help="Link command to be executed with options and arguments")

  args = parser.parse_args()

  log.setLevelVerboseOrQuiet(args.verbose, args.quiet)

  # Override defaults in settings.py with environment variables and RCfiles
  in_toto.user_settings.set_settings()

  # Regular signing and GPG signing are mutually exclusive
  if (args.key == None) == (args.gpg == None):
    parser.print_usage()
    parser.error("Specify either `--key <key path>` or `--gpg [<keyid>]`")

  # If `--gpg` was set without argument it has the value `True` and
  # we will try to sign with the default key
  gpg_use_default = (args.gpg == True)

  # Otherwise we interpret it as actual keyid
  gpg_keyid = None
  if args.gpg != True:
    gpg_keyid = args.gpg

  # If no_command is specified run in_toto_run without executing a command
  if args.no_command:
    args.link_cmd = []

  elif not args.link_cmd: # pragma: no branch
    parser.print_usage()
    parser.error("No command specified."
        " Please specify (or use the --no-command option)")


  try:
    # We load the key here because it might prompt the user for a password in
    # case the key is encrypted. Something that should not happen in the lib.
    key = None
    if args.key:
      key = util.prompt_import_rsa_key_from_file(args.key)

    runlib.in_toto_run(args.step_name, args.materials, args.products,
        args.link_cmd, args.record_streams, key, gpg_keyid, gpg_use_default,
        args.gpg_home)

  except Exception as e:
    log.error("(in-toto-run) - {0}: {1}".format(type(e).__name__, e))
    sys.exit(1)

  sys.exit(0)


if __name__ == "__main__":
  main()
