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

<Help>
usage: in-toto-record [-h] {start,stop} ...

Creates a signed link metadata file in two steps, in order to provide evidence
for supply chain steps that cannot be carried out by a single command (for
which 'in-toto-run' should be used). Returns nonzero value on failure and zero
otherwise.

positional arguments:
  {start,stop}
    start       Creates a preliminary link file recording the paths and hashes
                of the passed materials and signs it with the passed
                functionary's key. The resulting link file is stored as
                '.<name>.<keyid prefix>.link-unfinished'.
    stop        Expects a preliminary link file '.<name>.<keyid prefix>.link-
                unfinished' in the CWD, signed by the passed functionary's
                key. If found, it records and adds the paths and hashes of the
                passed products to the link metadata file, updates the
                signature and renames the file to '<name>.<keyid
                prefix>.link'.

optional arguments:
  -h, --help            show this help message and exit
  -k <path>, --key <path>
                        Path to a PEM formatted private key file used to sign
                        the resulting link metadata. (passing one of '--key'
                        or '--gpg' is required)
  -t {ed25519,rsa}, --key-type {ed25519,rsa}
                        Specify the key-type of the key specified by the
                        '--key' option. If '--key-type' is not passed, default
                        is "rsa".
  -g [<id>], --gpg [<id>]
                        GPG keyid used to sign the resulting link metadata.
                        When '--gpg' is passed without keyid, the keyring's
                        default GPG key is used. (passing one of '--key' or '
                        --gpg' is required)
  --gpg-home <path>     Path to GPG keyring to load GPG key identified by '--
                        gpg' option. If '--gpg-home' is not passed, the
                        default GPG keyring is used.
  --exclude <pattern> [<pattern> ...]
                        Do not record 'materials/products' that match one of
                        <pattern>. Passed exclude patterns override previously
                        set patterns, using e.g.: environment variables or
                        RCfiles. See ARTIFACT_EXCLUDE_PATTERNS documentation
                        for additional info.
  --base-path <path>    Record 'materials/products' relative to <path>. If not
                        set, current working directory is used as base path.
  --lstrip-paths <path> [<path> ...]
                        Record the path of artifacts in link metadata after
                        left stripping the specified <path> from the full
                        path. If there are multiple prefixes specified, only a
                        single prefix can match the path of any artifact and
                        that is then left stripped. All prefixes are checked
                        to ensure none of them are a left substring of another.
  -v, --verbose         Verbose execution.
  -q, --quiet           Suppress all output.

optional arguments (start subcommand only):
  -m <path> [<path> ...], --materials <path> [<path> ...]
                        Paths to files or directories, whose paths and hashes
                        are stored in the resulting link metadata's material
                        section when running the 'start' subcommand. Symlinks
                        are followed.

optional arguments (stop subcommand only):
  -p <path> [<path> ...], --products <path> [<path> ...]
                        Paths to files or directories, whose paths and hashes
                        are stored in the resulting link metadata's product
                        section when running the 'stop' subcommand. Symlinks
                        are followed.

required named arguments:
  -n <name>, --step-name <name>
                        Name used to associate the resulting link metadata
                        with the corresponding step defined in an in-toto
                        layout.

examples:
  Create link metadata file in two commands, signing it with the private key
  loaded from 'key_file', recording all files in the CWD as materials (on
  start), and as products (on stop).

    in-toto-record start -n edit-files -k path/to/key_file -m .
    in-toto-record stop -n edit-files -k path/to/key_file -p .


  Create link metadata file signed with the default GPG key from the default
  GPG keychain and record a file named 'foo' as material and product.

    in-toto-record start -n edit-foo --gpg -m path/to/foo
    in-toto-record stop -n edit-foo --gpg -p path/to/foo

"""
import sys
import argparse
import logging
import in_toto.util
import in_toto.user_settings
import in_toto.runlib

from in_toto.common_args import (EXCLUDE_ARGS, EXCLUDE_KWARGS,
    BASE_PATH_ARGS, BASE_PATH_KWARGS, LSTRIP_PATHS_ARGS,
    LSTRIP_PATHS_KWARGS)

# Command line interfaces should use in_toto base logger (c.f. in_toto.log)
log = logging.getLogger("in_toto")


def main():
  """Parse arguments, load key from disk (if passed) and call
  either runlib.in_toto_record_start or runlib.in_toto_record_stop depending
  on the specified subcommand. """

  parser = argparse.ArgumentParser(
      formatter_class=argparse.RawDescriptionHelpFormatter,
      description="""
Creates a signed link metadata file in two steps, in order to provide evidence
for supply chain steps that cannot be carried out by a single command (for
which 'in-toto-run' should be used). Returns nonzero value on failure and zero
otherwise.""")

  parser.epilog = """
examples:
  Create link metadata file in two commands, signing it with the private key
  loaded from 'key_file', recording all files in the CWD as materials (on
  start), and as products (on stop).

    {prog} start -n edit-files -k path/to/key_file -m .
    {prog} stop -n edit-files -k path/to/key_file -p .


  Create link metadata file signed with the default GPG key from the default
  GPG keychain and record a file named 'foo' as material and product.

    {prog} start -n edit-foo --gpg -m path/to/foo
    {prog} stop -n edit-foo --gpg -p path/to/foo

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
      "Name used to associate the resulting link metadata with the"
      " corresponding step defined in an in-toto layout."))

  # Either a key or a gpg key id have to be specified but not both
  key_args_group = parent_parser.add_mutually_exclusive_group(required=True)
  key_args_group.add_argument("-k", "--key", type=str, metavar="<path>", help=(
      "Path to a PEM formatted private key file used to sign the resulting"
      " link metadata."
      " (passing one of '--key' or '--gpg' is required)"))

  parent_parser.add_argument("-t", "--key-type", dest="key_type",
      type=str, choices=in_toto.util.SUPPORTED_KEY_TYPES,
      default=in_toto.util.KEY_TYPE_RSA, help=(
      "Specify the key-type of the key specified by the '--key' option. If"
      " '--key-type' is not passed, default is \"rsa\"."))

  key_args_group.add_argument("-g", "--gpg", nargs="?", const=True,
      metavar="<id>", help=(
      "GPG keyid used to sign the resulting link metadata.  When '--gpg' is"
      " passed without keyid, the keyring's default GPG key is used."
      " (passing one of '--key' or '--gpg' is required)"))

  parent_parser.add_argument("--gpg-home", dest="gpg_home", type=str,
      metavar="<path>", help=(
      "Path to GPG keyring to load GPG key identified by '--gpg' option.  If"
      " '--gpg-home' is not passed, the default GPG keyring is used."))

  parent_parser.add_argument(*EXCLUDE_ARGS, **EXCLUDE_KWARGS)
  parent_parser.add_argument(*BASE_PATH_ARGS, **BASE_PATH_KWARGS)
  parent_parser.add_argument(*LSTRIP_PATHS_ARGS, **LSTRIP_PATHS_KWARGS)


  verbosity_args = parent_parser.add_mutually_exclusive_group(required=False)
  verbosity_args.add_argument("-v", "--verbose", dest="verbose",
      help="Verbose execution.", action="store_true")

  verbosity_args.add_argument("-q", "--quiet", dest="quiet",
      help="Suppress all output.", action="store_true")

  subparser_start = subparsers.add_parser("start", parents=[parent_parser],
      help=(
      "Creates a preliminary link file recording the paths and hashes of"
      " the passed materials and signs it with the passed functionary's"
      " key. The resulting link file is stored as"
      " '.<name>.<keyid prefix>.link-unfinished'."))

  subparser_stop = subparsers.add_parser("stop", parents=[parent_parser],
      help=(
      "Expects a preliminary link file '.<name>.<keyid prefix>.link-unfinished'"
      " in the CWD, signed by the passed functionary's key. If found, it"
      " records and adds the paths and hashes of the passed products to the"
      " link metadata file, updates the signature and renames the file to"
      " '<name>.<keyid prefix>.link'."))

  subparser_start.add_argument("-m", "--materials", type=str, required=False,
      nargs='+', metavar="<path>", help=(
      "Paths to files or directories, whose paths and hashes are stored in the"
      " resulting link metadata's material section when running the 'start'"
      " subcommand. Symlinks are followed."))

  subparser_stop.add_argument("-p", "--products", type=str, required=False,
      nargs='+', metavar="<path>", help=(
      "Paths to files or directories, whose paths and hashes are stored in the"
      " resulting link metadata's product section when running the 'stop'"
      " subcommand. Symlinks are followed."))

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

  try:
    # We load the key here because it might prompt the user for a password in
    # case the key is encrypted. Something that should not happen in the lib.
    key = None
    if args.key:
      key = in_toto.util.import_private_key_from_file(args.key, args.key_type)

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
          lstrip_paths=args.lstrip_paths)

  except Exception as e:
    log.error("(in-toto-record {0}) {1}: {2}"
        .format(args.command, type(e).__name__, e))
    sys.exit(1)

  sys.exit(0)

if __name__ == "__main__":
  main()
