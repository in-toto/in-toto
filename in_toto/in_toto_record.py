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
import os
import sys
import argparse
import in_toto.util
from in_toto import runlib
from in_toto import log

def in_toto_record_start(step_name, key, material_list):
  """
  <Purpose>
    Calls runlib.in_toto_record_start and handles exceptions

  <Arguments>
    step_name:
            A unique name to relate link metadata with a step defined in the
            layout.
    key:
            Private key to sign link metadata.
            Format is securesystemslib.formats.KEY_SCHEMA
    material_list:
            List of file or directory paths that should be recorded as
            materials.

  <Exceptions>
    SystemExit if any exception occurs

  <Side Effects>
    Calls sys.exit(1) if an exception is raised

  <Returns>
    None.

  """
  try:
    runlib.in_toto_record_start(step_name, key, material_list)
  except Exception as e:
    log.error("in start record - {}".format(e))
    sys.exit(1)

def in_toto_record_stop(step_name, key, product_list):
  """
  <Purpose>
    Calls runlib.in_toto_record_stop and handles exceptions


  <Arguments>
    step_name:
            A unique name to relate link metadata with a step defined in the
            layout.
    key:
            Private key to sign link metadata.
            Format is securesystemslib.formats.KEY_SCHEMA
    product_list:
            List of file or directory paths that should be recorded as products.

  <Exceptions>
    SystemExit if any exception occurs

  <Side Effects>
    Calls sys.exit(1) if an exception is raised

  <Returns>
    None.

  """
  try:
    runlib.in_toto_record_stop(step_name, key, product_list)
  except Exception as e:
    log.error("in stop record - {}".format(e))
    sys.exit(1)

def main():
  """ Parse arguments, load key from disk and call either in_toto_record_start
  or in_toto_record_stop. """
  parser = argparse.ArgumentParser(
      description="Starts or stops link metadata recording")

  subparsers = parser.add_subparsers(dest="command")

  subparser_start = subparsers.add_parser('start')
  subparser_stop = subparsers.add_parser('stop')

  # Whitespace padding to align with program name
  lpad = (len(parser.prog) + 1) * " "
  parser.usage = ("\n"
      "%(prog)s  --step-name <unique step name>\n{0}"
               " --key <functionary private key path>\n"
               "[--verbose]\n"
      "Commands:\n{0}"
               "start [--materials <filepath>[ <filepath> ...]]\n{0}"
               "stop  [--products <filepath>[ <filepath> ...]]\n"
               .format(lpad))

  in_toto_args = parser.add_argument_group("in-toto options")
  # FIXME: Do we limit the allowed characters for the name?
  in_toto_args.add_argument("-n", "--step-name", type=str, required=True,
      help="Unique name for link metadata")

  in_toto_args.add_argument("-k", "--key", type=str, required=True,
      help="Path to private key to sign link metadata (PEM)")

  in_toto_args.add_argument("-v", "--verbose", dest='verbose',
      help="Verbose execution.", default=False, action='store_true')

  subparser_start.add_argument("-m", "--materials", type=str, required=False,
      nargs='+', help="Files to record before link command execution")

  subparser_stop.add_argument("-p", "--products", type=str, required=False,
      nargs='+', help="Files to record after link command execution")

  args = parser.parse_args()

  # Turn on all the `log.info()` in the library
  if args.verbose:
    log.logging.getLogger().setLevel(log.logging.INFO)

  # We load the key here because it might prompt the user for a password in
  # case the key is encrypted. Something that should not happen in the library.
  try:
    key = in_toto.util.prompt_import_rsa_key_from_file(args.key)
  except Exception as e:
    log.error("in load key - {}".format(args.key))
    sys.exit(1)

  if args.command == "start":
    in_toto_record_start(args.step_name, key, args.materials)
  elif args.command == "stop":
    in_toto_record_stop(args.step_name, key, args.products)

if __name__ == '__main__':
  main()
