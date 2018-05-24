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
  Provides a command line interface for runlib.in_toto_run.

<Return Codes>
  2 if an exception occurred during argument parsing
  1 if an exception occurred
  0 if no exception occurred

<Help>
usage: in-toto-run <named arguments> [optional arguments] -- <command> [args]

Executes the passed command and records paths and hashes of 'materials' (i.e.
files before command execution) and 'products' (i.e. files after command
execution) and stores them together with other information (executed command,
return value, stdout, stderr, ...) to a link metadata file, which is signed
with the passed key.  Returns nonzero value on failure and zero otherwise.

positional arguments:
  <command>             Command to be executed with options and arguments,
                        separated from 'in-toto-run' options by double dash
                        '--'.

optional arguments:
  -h, --help            show this help message and exit
  -m <path> [<path> ...], --materials <path> [<path> ...]
                        Paths to files or directories, whose paths and hashes
                        are stored in the resulting link metadata before the
                        command is executed. Symlinks are followed.
  -p <path> [<path> ...], --products <path> [<path> ...]
                        Paths to files or directories, whose paths and hashes
                        are stored in the resulting link metadata after the
                        command is executed. Symlinks are followed.
  --gpg-home <path>     Path to GPG keyring to load GPG key identified by '--
                        gpg' option. If '--gpg-home' is not passed, the
                        default GPG keyring is used.
  -b, --record-streams  If passed 'stdout' and 'stderr' of the executed
                        command are redirected and stored in the resulting
                        link metadata.
  -x, --no-command      Generate link metadata without executing a command,
                        e.g. for a 'signed off by' step.
  --exclude <pattern> [<pattern> ...]
                        Do not record 'materials/products' that match one of
                        <pattern>. Passed exclude patterns override previously
                        set patterns, using e.g.: environment variables or
                        RCfiles. See ARTIFACT_EXCLUDE_PATTERNS documentation
                        for additional info.
  --base-path <path>    Record 'materials/products' relative to <path>. If not
                        set, current working directory is used as base path.
  -t {ed25519,rsa}, --key-type {ed25519,rsa}
                        Specify the key-type of the key specified by the
                        '--key' option. If '--key-type' is not passed, default
                        is "rsa".
  -v, --verbose         Verbose execution.
  -q, --quiet           Suppress all output.

required named arguments:
  -n <name>, --step-name <name>
                        Name used to associate the resulting link metadata
                        with the corresponding step defined in an in-toto
                        layout.
  -k <path>, --key <path>
                        Path to a PEM formatted private key file used to sign
                        the resulting link metadata. (passing one of '--key'
                        or '--gpg' is required)
  -g [<id>], --gpg [<id>]
                        GPG keyid used to sign the resulting link metadata.
                        When '--gpg' is passed without keyid, the keyring's
                        default GPG key is used. (passing one of '--key' or '
                        --gpg' is required)

examples:
  Tag a git repo, storing files in CWD as products, signing the resulting link
  file with the private key loaded from 'key_file'.

      in-toto-run -n tag -p . -k key_file -- git tag v1.0


  Create tarball, storing files in 'project' directory as materials and the
  tarball as product, signing the link file with GPG key '...7E0C8A17'.

      in-toto-run -n package -m project -p project.tar.gz \
             -g 8465A1E2E0FB2B40ADB2478E18FB3F537E0C8A17 \
             -- tar czf project.tar.gz project

"""

import sys
import argparse
import logging
import in_toto.user_settings
from in_toto import (util, runlib)

from in_toto.common_args import (EXCLUDE_ARGS, EXCLUDE_KWARGS,
    BASE_PATH_ARGS, BASE_PATH_KWARGS)

# Command line interfaces should use in_toto base logger (c.f. in_toto.log)
log = logging.getLogger("in_toto")


def main():
  """Parse arguments, load key from disk (prompts for password if key is
  encrypted) and call in_toto_run. """

  parser = argparse.ArgumentParser(
      formatter_class=argparse.RawDescriptionHelpFormatter,
      description="""
Executes the passed command and records paths and hashes of 'materials' (i.e.
files before command execution) and 'products' (i.e. files after command
execution) and stores them together with other information (executed command,
return value, stdout, stderr, ...) to a link metadata file, which is signed
with the passed key.  Returns nonzero value on failure and zero otherwise.""")

  parser.usage = ("%(prog)s <named arguments> [optional arguments]"
      " -- <command> [args]")

  parser.epilog = """
examples:
  Tag a git repo, storing files in CWD as products, signing the resulting link
  file with the private key loaded from 'key_file'.

      {prog} -n tag -p . -k key_file -- git tag v1.0


  Create tarball, storing files in 'project' directory as materials and the
  tarball as product, signing the link file with GPG key '...7E0C8A17'.

      {prog} -n package -m project -p project.tar.gz \\
             -g 8465A1E2E0FB2B40ADB2478E18FB3F537E0C8A17 \\
             -- tar czf project.tar.gz project

""".format(prog=parser.prog)


  named_args = parser.add_argument_group("required named arguments")

  # FIXME: Do we limit the allowed characters for the name?
  named_args.add_argument("-n", "--step-name", type=str, required=True,
      metavar="<name>", help=(
      "Name used to associate the resulting link metadata with the"
      " corresponding step defined in an in-toto layout."))

  parser.add_argument("-m", "--materials", type=str, required=False,
      nargs='+', metavar="<path>", help=(
      "Paths to files or directories, whose paths and hashes are stored in the"
      " resulting link metadata before the command is executed. Symlinks are"
      " followed."))

  parser.add_argument("-p", "--products", type=str, required=False,
      nargs='+', metavar="<path>", help=(
      "Paths to files or directories, whose paths and hashes are stored in the"
      " resulting link metadata after the command is executed. Symlinks are"
      " followed."))

  named_args.add_argument("-k", "--key", type=str, metavar="<path>", help=(
      "Path to a PEM formatted private key file used to sign the resulting"
      " link metadata."
      " (passing one of '--key' or '--gpg' is required)"))

  parser.add_argument("-t", "--key-type", dest="key_type", type=str,
      choices=util.SUPPORTED_KEY_TYPES, default=util.KEY_TYPE_RSA, help=(
      "Specify the key-type of the key specified by the '--key' option. If"
      " '--key-type' is not passed, default is \"ed25519\"."))

  named_args.add_argument("-g", "--gpg", nargs="?", const=True, metavar="<id>",
      help=(
      "GPG keyid used to sign the resulting link metadata.  When '--gpg' is"
      " passed without keyid, the keyring's default GPG key is used."
      " (passing one of '--key' or '--gpg' is required)"))

  parser.add_argument("--gpg-home", dest="gpg_home", type=str,
      metavar="<path>", help=(
      "Path to GPG keyring to load GPG key identified by '--gpg' option.  If"
      " '--gpg-home' is not passed, the default GPG keyring is used."))

  parser.add_argument("-s", "--record-streams", dest="record_streams",
      default=False, action="store_true", help=(
      "If passed 'stdout' and 'stderr' of the executed command are redirected"
      " and stored in the resulting link metadata."))

  parser.add_argument("-x", "--no-command", dest="no_command", default=False,
    action="store_true", help=(
    "Generate link metadata without executing a command, e.g. for a 'signed"
    " off by' step."))

  parser.add_argument(*EXCLUDE_ARGS, **EXCLUDE_KWARGS)
  parser.add_argument(*BASE_PATH_ARGS, **BASE_PATH_KWARGS)

  verbosity_args = parser.add_mutually_exclusive_group(required=False)
  verbosity_args.add_argument("-v", "--verbose", dest="verbose",
      help="Verbose execution.", action="store_true")

  verbosity_args.add_argument("-q", "--quiet", dest="quiet",
      help="Suppress all output.", action="store_true")


  # FIXME: This is not yet ideal.
  # What should we do with tokens like > or ; ?
  parser.add_argument("link_cmd", nargs="*", metavar="<command>",
      help=(
      "Command to be executed with options and arguments, separated from"
      " 'in-toto-run' options by double dash '--'."))

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
      key = util.import_private_key_from_file(args.key, args.key_type)

    runlib.in_toto_run(args.step_name, args.materials, args.products,
        args.link_cmd, args.record_streams, key, gpg_keyid, gpg_use_default,
        args.gpg_home, args.exclude_patterns, args.base_path)

  except Exception as e:
    log.error("(in-toto-run) {0}: {1}".format(type(e).__name__, e))
    sys.exit(1)

  sys.exit(0)


if __name__ == "__main__":
  main()
