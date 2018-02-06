#!/usr/bin/env python
"""
<Program Name>
  in_toto_record.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Nov 28, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides a command line interface to create a link metadata file in two
  steps, in order to provide evidence for activities that can't be expressed
  by a single command (for which you should use in-toto-run).

  The commands to start and stop recording evidence are:

  start
    Creates a temporary link file containing the file hashes of the passed
    materials and signs it with the passed functionary's key under
    .<step name>.<keyid>.link-unfinished

  stop
    Expects a .<step name>.<keyid>.link-unfinished in the current directory
    signed by the passed functionary's key, adds the file hashes of the passed
    products, updates the signature and renames the file
    .<step name>.<keyid>.link-unfinished to <step name>.<keyid>.link

  The implementation of the tasks can be found in runlib.

<Example Usage>
  Create link file signed with specified 'key' stored on disk and record all
  files in current working directory as materials and products.
  Any files in the current working directory that you edit between running
  the commands will have different hashes in their corresponding material and
  product entries of the resulting link file 'edit-files.<keyid>.link'.

  ```
  in-toto-record start --step-name edit-files -key /path/to/key --materials .
  in-toto-record stop --step-name edit-files -key /path/to/key --products .
  ```

  # Create link file signed with the default gpg key and record a file named
  # 'foo' as material and product.
  # If you edit foo between running the commands the recorded hashes in the
  # resulting link file 'edit-foo.<keyid>.link' will differ.
  ```
  in-toto-record start --step-name edit-foo --gpg --materials path/to/foo
  in-toto-record stop --step-name edit-foo --gpg --products path/to/foo
  ```

"""
import sys
import argparse
import logging
import in_toto.util
import in_toto.user_settings
import in_toto.runlib

# Command line interfaces should use in_toto base logger (c.f. in_toto.log)
log = logging.getLogger("in_toto")


def main():
  """Parse arguments, load key from disk (if passed) and call
  either runlib.in_toto_record_start or runlib.in_toto_record_stop depending
  on the specified subcommand. """

  parser = argparse.ArgumentParser(
      description="Starts or stops link metadata recording")

  # The subparsers inherit the arguments from the parent parser
  parent_parser = argparse.ArgumentParser(add_help=False)
  subparsers = parser.add_subparsers(dest="command")

  # FIXME: Do we limit the allowed characters for the name?
  parent_parser.add_argument("-n", "--step-name", type=str, required=True,
      help="Unique name for link metadata", metavar="<unique step name>")

  # Either a key or a gpg key id have to be specified but not both
  key_args_group = parent_parser.add_mutually_exclusive_group(required=True)
  key_args_group.add_argument("-k", "--key", type=str,
      help="Path to private key to sign link metadata (PEM)",
      metavar="<signing key path>")
  key_args_group.add_argument("-g", "--gpg", nargs="?", const=True,
      metavar="<gpg keyid>", help=("GPG keyid to sign link metadata "
      "(if set without argument, the default key is used)"))

  parent_parser.add_argument("--gpg-home", dest="gpg_home", type=str,
      help="Path to GPG keyring (if not set the default keyring is used)",
      metavar="<gpg keyring path>")

  verbosity_args = parent_parser.add_mutually_exclusive_group(required=False)
  verbosity_args.add_argument("-v", "--verbose", dest="verbose",
      help="Verbose execution.", action="store_true")

  verbosity_args.add_argument("-q", "--quiet", dest="quiet",
      help="Suppress all output.", action="store_true")

  subparser_start = subparsers.add_parser("start", parents=[parent_parser])
  subparser_stop = subparsers.add_parser("stop", parents=[parent_parser])

  subparser_start.add_argument("-m", "--materials", type=str, required=False,
      nargs='+', help="Files to record before link command execution",
      metavar="<material path>")

  subparser_stop.add_argument("-p", "--products", type=str, required=False,
      nargs='+', help="Files to record after link command execution",
      metavar="<product path>")

  args = parser.parse_args()

  log.setLevelVerboseOrQuiet(args.verbose, args.quiet)

  # Override defaults in settings.py with environment variables and RCfiles
  in_toto.user_settings.set_settings()

  # If `--gpg` was set without argument it has the value `True` and
  # we will try to sign with the default key
  gpg_use_default = (args.gpg == True)

  # Otherwise gpg_keyid stays either None or gets the passed argument assigned
  gpg_keyid = None
  if not gpg_use_default and args.gpg:
    gpg_keyid = args.gpg

  # We load the key here because it might prompt the user for a password in
  # case the key is encrypted. Something that should not happen in the library.
  key = None
  if args.key:
    try:
      key = in_toto.util.prompt_import_rsa_key_from_file(args.key)

    except Exception as e:
      log.error("in load key - {}".format(e))
      sys.exit(1)

  try:
    if args.command == "start":
      in_toto.runlib.in_toto_record_start(args.step_name, args.materials,
          signing_key=key, gpg_keyid=gpg_keyid,
          gpg_use_default=gpg_use_default, gpg_home=args.gpg_home)

    # Mutually exclusiveness is guaranteed by argparser
    else: # args.command == "stop":
      in_toto.runlib.in_toto_record_stop(args.step_name, args.products,
          signing_key=key, gpg_keyid=gpg_keyid,
          gpg_use_default=gpg_use_default, gpg_home=args.gpg_home)

  except Exception as e:
    log.error("in {} record - {}".format(args.command, e))
    sys.exit(1)

  sys.exit(0)

if __name__ == "__main__":
  main()
