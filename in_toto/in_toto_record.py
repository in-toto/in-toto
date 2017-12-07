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
  Provides a command line interface to start and stop in-toto link metadata
  recording.

  start
    Takes a step name, a functionary's signing key and optional
    material paths.
    Creates a temporary link file containing the file hashes of the passed
    materials and signs it with the functionary's key under
    .<step name>.link-unfinished

  stop
    Takes a step name, a functionary's signing key and optional
    product paths.
    Expects a .<step name>.link-unfinished in the current directory signed by
    the functionary's signing key, adds the file hashes of the passed products,
    updates the signature and renames the file  .<step name>.link-unfinished
    to <step name>.link


  The implementation of the tasks can be found in runlib.

  Example Usage
  ```
  in-toto-record --step-name edit-files start --materials . --key bob
  # Edit files manually ...
  in-toto-record --step-name edit-files stop --products . --key bob
  ```

"""
import sys
import argparse
import in_toto.util
import in_toto.user_settings
import in_toto.runlib
import in_toto.log

def main():
  """ Parse arguments, load key from disk and call either in_toto_record_start
  or in_toto_record_stop. """
  parser = argparse.ArgumentParser(
      description="Starts or stops link metadata recording")

  # The subparsers inherit the arguments from the parent parser
  parent_parser = argparse.ArgumentParser(add_help=False)
  subparsers = parser.add_subparsers(dest="command")

  # FIXME: Do we limit the allowed characters for the name?
  parent_parser.add_argument("-n", "--step-name", type=str, required=True,
      help="Unique name for link metadata", metavar="<unique step name>")

  parent_parser.add_argument("-k", "--key", type=str, required=True,
      help="Path to private key to sign link metadata (PEM)",
      metavar="<signing key path>")

  parent_parser.add_argument("-v", "--verbose", dest="verbose",
      help="Verbose execution.", default=False, action="store_true")

  subparser_start = subparsers.add_parser("start", parents=[parent_parser])
  subparser_stop = subparsers.add_parser("stop", parents=[parent_parser])

  subparser_start.add_argument("-m", "--materials", type=str, required=False,
      nargs='+', help="Files to record before link command execution",
      metavar="<material path>")

  subparser_stop.add_argument("-p", "--products", type=str, required=False,
      nargs='+', help="Files to record after link command execution",
      metavar="<product path>")

  args = parser.parse_args()

  # Turn on all the `log.info()` in the library
  if args.verbose:
    in_toto.log.logging.getLogger().setLevel(in_toto.log.logging.INFO)

  # Override defaults in settings.py with environment variables and RCfiles
  in_toto.user_settings.set_settings()

  # We load the key here because it might prompt the user for a password in
  # case the key is encrypted. Something that should not happen in the library.
  try:
    key = in_toto.util.prompt_import_rsa_key_from_file(args.key)
  except Exception as e:
    in_toto.log.error("in load key - {}".format(e))
    sys.exit(1)

  try:
    if args.command == "start":
      in_toto.runlib.in_toto_record_start(args.step_name, args.materials, key)

    elif args.command == "stop": # pragma: no branch
      in_toto.runlib.in_toto_record_stop(args.step_name, args.products, key)

    # Else is caught by argparser

  except Exception as e:
    in_toto.log.error("in {} record - {}".format(args.command, e))
    sys.exit(1)

if __name__ == '__main__':
  main()
