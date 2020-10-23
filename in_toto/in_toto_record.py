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
  Provides a command line interface for runlib.in_toto_record_start and
  runlib.in_toto_record_stop.

<Return Codes>
  2 if an exception occurred during argument parsing
  1 if an exception occurred
  0 if no exception occurred

"""
import sys
import argparse
import logging
import in_toto.user_settings
import in_toto.runlib
from in_toto import __version__

from in_toto.common_args import (EXCLUDE_ARGS, EXCLUDE_KWARGS, BASE_PATH_ARGS,
    BASE_PATH_KWARGS, LSTRIP_PATHS_ARGS, LSTRIP_PATHS_KWARGS, KEY_ARGS,
    KEY_KWARGS, KEY_TYPE_KWARGS, KEY_TYPE_ARGS, GPG_ARGS, GPG_KWARGS,
    GPG_HOME_ARGS, GPG_HOME_KWARGS, VERBOSE_ARGS, VERBOSE_KWARGS, QUIET_ARGS,
    QUIET_KWARGS, METADATA_DIRECTORY_ARGS, METADATA_DIRECTORY_KWARGS,
    KEY_PASSWORD_ARGS, KEY_PASSWORD_KWARGS, parse_password_and_prompt_args,
    sort_action_groups, title_case_action_groups)

from securesystemslib import interface


# Command line interfaces should use in_toto base logger (c.f. in_toto.log)
LOG = logging.getLogger("in_toto")


def create_parser():
  """Create and return configured ArgumentParser instance. """

  parser = argparse.ArgumentParser(
      formatter_class=argparse.RawDescriptionHelpFormatter,
      description="""
in-toto-record creates a signed link metadata file in two steps, in order to
provide evidence for supply chain steps that cannot be carried out by a single
command (for which 'in-toto-run' should be used). It returns a non-zero value
on failure and zero otherwise.""")

  parser.epilog = """EXAMPLE USAGE

Create link metadata file in two commands, signing it with the private key
loaded from 'key_file', recording all files in the CWD as materials (on
start), and as products (on stop).

  {prog} start -n edit-files -k path/to/key_file -m .
  {prog} stop -n edit-files -k path/to/key_file -p .


Create link metadata file signed with the default GPG key from the default
GPG home directory and record a file named 'foo' as material and product.

  {prog} start -n edit-foo --gpg -m path/to/foo
  {prog} stop -n edit-foo --gpg -p path/to/foo


Create link metadata file signed with the private key loaded from 'key_file',
record all files in the CWD as material and product, and dump finished link
file to the target directory (on stop).

  {prog} start -n edit-files -k path/to/key_file -m .
  {prog} stop -d path/to/target/dir -n edit-files -k path/to/key_file -p .

""".format(prog=parser.prog)

  # The subparsers inherit the arguments from the parent parser
  parent_parser = argparse.ArgumentParser(add_help=False)
  subparsers = parser.add_subparsers(dest="command")

  # Workaround to make subcommands mandatory in Python>=3.3
  # https://bugs.python.org/issue9253#msg186387
  subparsers.required = True

  parent_named_args = parent_parser.add_argument_group(
      "required named arguments")

  # FIXME: Do we limit the allowed characters for the name?
  parent_named_args.add_argument("-n", "--step-name", type=str, required=True,
      metavar="<name>", help=(
      "name for the resulting link metadata file. It is also used to associate"
      " the link with a step defined in an in-toto layout."))

  parent_named_args.add_argument(*KEY_ARGS, **KEY_KWARGS)
  parent_parser.add_argument(*KEY_TYPE_ARGS, **KEY_TYPE_KWARGS)
  parent_parser.add_argument(*KEY_PASSWORD_ARGS, **KEY_PASSWORD_KWARGS)

  parent_named_args.add_argument(*GPG_ARGS, **GPG_KWARGS)
  parent_parser.add_argument(*GPG_HOME_ARGS, **GPG_HOME_KWARGS)

  parent_parser.add_argument(*EXCLUDE_ARGS, **EXCLUDE_KWARGS)
  parent_parser.add_argument(*BASE_PATH_ARGS, **BASE_PATH_KWARGS)
  parent_parser.add_argument(*LSTRIP_PATHS_ARGS, **LSTRIP_PATHS_KWARGS)

  verbosity_args = parent_parser.add_mutually_exclusive_group(required=False)
  verbosity_args.add_argument(*VERBOSE_ARGS, **VERBOSE_KWARGS)
  verbosity_args.add_argument(*QUIET_ARGS, **QUIET_KWARGS)

  subparser_start = subparsers.add_parser("start", parents=[parent_parser],
      help=(
      "creates a preliminary link file recording the paths and hashes of"
      " the passed materials and signs it with the passed functionary's"
      " key. The resulting link file is stored as"
      " '.<name>.<keyid prefix>.link-unfinished'."))

  subparser_stop = subparsers.add_parser("stop", parents=[parent_parser],
      help=(
      "expects preliminary link file '.<name>.<keyid prefix>.link-unfinished'"
      " in the CWD, signed by the passed functionary's key. If found, it"
      " records and adds the paths and hashes of the passed products to the"
      " link metadata file, updates the signature and renames the file to"
      " '<name>.<keyid prefix>.link'."))

  subparser_start.add_argument("-m", "--materials", type=str, required=False,
      nargs='+', metavar="<path>", help=(
      "paths to files or directories, whose paths and hashes are stored in the"
      " resulting link metadata's material section when running the 'start'"
      " subcommand. Symlinks to files are followed."))

  subparser_stop.add_argument("-p", "--products", type=str, required=False,
      nargs='+', metavar="<path>", help=(
      "paths to files or directories, whose paths and hashes are stored in the"
      " resulting link metadata's product section when running the 'stop'"
      " subcommand. Symlinks to files are followed."))

  subparser_stop.add_argument(*METADATA_DIRECTORY_ARGS,
      **METADATA_DIRECTORY_KWARGS)

  parser.add_argument('--version', action='version',
                      version='{} {}'.format(parser.prog, __version__))

  for _parser, _order in [
      (parser, ["Positional Arguments", "Optional Arguments"]),
      (subparser_start, None), (subparser_stop, None)]:
    title_case_action_groups(_parser)
    sort_action_groups(_parser, _order)

  return parser


def main():
  """Parse arguments, load key from disk (if passed) and call
  either runlib.in_toto_record_start or runlib.in_toto_record_stop depending
  on the specified subcommand. """

  parser = create_parser()
  args = parser.parse_args()

  LOG.setLevelVerboseOrQuiet(args.verbose, args.quiet)

  # Override defaults in settings.py with environment variables and RCfiles
  in_toto.user_settings.set_settings()

  # Regular signing and GPG signing are mutually exclusive
  if (args.key is None) == (args.gpg is None):
    parser.print_usage()
    parser.error("Specify either '--key <key path>' or '--gpg [<keyid>]'")

  password, prompt = parse_password_and_prompt_args(args)

  # If `--gpg` was set without argument it has the value `True` and
  # we will try to sign with the default key
  gpg_use_default = (args.gpg is True)

  # Otherwise gpg_keyid stays either None or gets the passed argument assigned
  gpg_keyid = None
  if not gpg_use_default and args.gpg:
    gpg_keyid = args.gpg

  try:
    # We load the key here because it might prompt the user for a password in
    # case the key is encrypted. Something that should not happen in the lib.
    key = None
    if args.key:
      key = interface.import_privatekey_from_file(
          args.key, key_type=args.key_type, password=password, prompt=prompt)

    if args.command == "start":
      in_toto.runlib.in_toto_record_start(args.step_name, args.materials,
          signing_key=key, gpg_keyid=gpg_keyid,
          gpg_use_default=gpg_use_default, gpg_home=args.gpg_home,
          exclude_patterns=args.exclude_patterns, base_path=args.base_path,
          lstrip_paths=args.lstrip_paths)

    # Mutually exclusiveness is guaranteed by argparser
    else: # args.command == "stop":
      in_toto.runlib.in_toto_record_stop(args.step_name, args.products,
          signing_key=key, gpg_keyid=gpg_keyid,
          gpg_use_default=gpg_use_default, gpg_home=args.gpg_home,
          exclude_patterns=args.exclude_patterns, base_path=args.base_path,
          lstrip_paths=args.lstrip_paths,
          metadata_directory=args.metadata_directory)

  except Exception as e:
    LOG.error("(in-toto-record {0}) {1}: {2}"
        .format(args.command, type(e).__name__, e))
    sys.exit(1)

  sys.exit(0)

if __name__ == "__main__":
  main()
