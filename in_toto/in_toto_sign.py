#!/usr/bin/env python
"""
<Program Name>
  in_toto_sign.py

<Author>
  Sachit Malik <i.sachitmalik@gmail.com>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  June 13, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides command line interface to sign in-toto link or layout metadata
  or to verify its signatures.

<Help>
usage: in-toto-sign [-h] -f <path> [-k <path> [<path> ...]]
                    [-t <key_type> [<key_type> ...]] [-g [<id> [<id> ...]]]
                    [--gpg-home <path>] [-o <path>] [-a] [--verify] [-v | -q]

Provides command line interface to sign in-toto link or layout metadata or
verify its signatures, with options to:

  * replace (default) or add signature(s):
    + layout metadata can be signed by multiple keys at once,
    + link metadata can only be signed by one key at a time.

  * write signed metadata to a specified path. If no output path is specified,
    + layout metadata is written to the path of the input file,
    + link metadata is written to '<name>.<keyid prefix>.link'.

  * verify signatures

Returns nonzero value on failure and zero otherwise.

optional arguments:
  -h, --help            show this help message and exit
  -k <path> [<path> ...], --key <path> [<path> ...]
                        Path(s) to PEM formatted key file(s), used to sign the
                        passed link or layout metadata or to verify its
                        signatures.
  -t <key_type> [<key_type> ...], --key-type <key_type> [<key_type> ...]
                        Specify the key-type of the keys specified by the
                        '--key' option. Number of values should be the same as
                        the number of keys specified by the '--key' option. If
                        '--key-type' is not passed, default key_type of all
                        keys is assumed to be \"rsa\".
  -g [<id> [<id> ...]], --gpg [<id> [<id> ...]]
                        GPG keyid used to sign the passed link or layout
                        metadata or to verify its signatures. If passed
                        without keyid, the default GPG key is used.
  --gpg-home <path>     Path to GPG keyring to load GPG key identified by '--
                        gpg' option. If '--gpg-home' is not passed, the
                        default GPG keyring is used.
  -o <path>, --output <path>
                        Path to store metadata file to be signed. If not
                        passed, layout metadata is written to the path of the
                        input file and link metadata is written to '<step
                        name>.<keyid prefix>.link'
  -a, --append          If passed, signatures are added rather than replacing
                        existing signatures. This option is only availabe for
                        layout metdata.
  --verify              Verify signature(s) of passed link or layout metadata.
  -v, --verbose         Verbose execution.
  -q, --quiet           Suppress all output.

required named arguments:
  -f <path>, --file <path>
                        Path to link or layout file to be signed or verified.

examples:
  Append two signatures to 'unsigned.layout' file and write to 'root.layout'.

      in-toto-sign -f unsigned.layout -k priv_key1 priv_key2 -o root.layout -a


  Replace signature in link file. And write to default filename, i.e.
  'package.<priv_key's keyid prefix>.link'.

      in-toto-sign -f package.2f89b927.link -k priv_key


  Verify layout signed with 3 keys.

      in-toto-sign -f root.layout -k pub_key0 pub_key1 pub_key2 --verify


  Sign layout with default gpg key in default gpg keyring.

      in-toto-sign -f root.layout --gpg


  Verify layout with a gpg key identified by keyid '...439F3C2'.

      in-toto-sign -f root.layout --verify \
      --gpg 3BF8135765A07E21BD12BF89A5627F6BF439F3C2

"""
import sys
import six
import argparse
import logging

from in_toto import exceptions, util
from in_toto.models.link import FILENAME_FORMAT
from in_toto.models.metadata import Metablock
import in_toto.gpg.functions

import securesystemslib.formats


# Command line interfaces should use in_toto base logger (c.f. in_toto.log)
log = logging.getLogger("in_toto")


def _sign_and_dump_metadata(metadata, args):
  """
  <Purpose>
    Internal method to sign link or layout metadata and dump it to disk.

  <Arguments>
    metadata:
            Metablock object (contains Link or Layout object)
    args:
            see argparser

  <Exceptions>
    SystemExit(0) if signing is successful
    SystemExit(2) if any exception occurs

  """

  try:
    if not args.append:
      metadata.signatures = []

    signature = None
    # If the cli tool was called with `--gpg [KEYID ...]` `args.gpg` is
    # a list (not None) and we will try to sign with gpg.
    # If `--gpg-home` was not set, args.gpg_home is None and the signer tries
    # to use the default gpg keyring.
    if args.gpg != None:
      # If `--gpg` was passed without argument we sign with the default key
      # Excluded so that coverage does not vary in different test environments
      if len(args.gpg) == 0: # pragma: no cover
        signature = metadata.sign_gpg(gpg_keyid=None, gpg_home=args.gpg_home)

      # Otherwise we sign with each passed keyid
      for keyid in args.gpg:
        securesystemslib.formats.KEYID_SCHEMA.check_match(keyid)
        signature = metadata.sign_gpg(gpg_keyid=keyid, gpg_home=args.gpg_home)

    # Alternatively we iterate over passed private key paths `--key KEYPATH ...`
    # load the corresponding key from disk and sign with it
    elif args.key != None: # pragma: no branch

      if args.key_type is None:
        args.key_type = [util.KEY_TYPE_RSA] * len(args.key)

      if len(args.key_type) != len(args.key):
        raise securesystemslib.exceptions.FormatError(
          "number of key_types should match with the number"
          " of keys specified")

      for idx, key_path in enumerate(args.key):
        key = util.import_private_key_from_file(key_path, args.key_type[idx])
        signature = metadata.sign(key)

    # If `--output` was specified we store the signed link or layout metadata
    # to that location no matter what
    if args.output:
      out_path = args.output

    # Otherwise, in case of links, we build the filename using the link/step
    # name and the keyid of the created signature (there is only one for links)
    elif metadata.type_ == "link":
      in_toto.formats.ANY_SIGNATURE_SCHEMA.check_match(signature)
      keyid = signature["keyid"]
      out_path = FILENAME_FORMAT.format(step_name=metadata.signed.name,
          keyid=keyid)

    # In case of layouts we just override the input file.
    elif metadata.type_ == "layout": # pragma: no branch
      out_path = args.file

    log.info("Dumping {0} to '{1}'...".format(metadata.type_, out_path))

    metadata.dump(out_path)
    sys.exit(0)

  except Exception as e:
    log.error("The following error occurred while signing: "
        "{}".format(e))
    sys.exit(2)


def _verify_metadata(metadata, args):
  """
  <Purpose>
    Internal method to verify link or layout signatures.

  <Arguments>
    metadata:
            Metablock object (contains Link or Layout object)
    args:
            see argparser

  <Exceptions>
    SystemExit(0) if verification passes
    SystemExit(1) if verification fails
    SystemExit(2) if any exception occurs

  """
  try:
    # Load pubkeys from disk ....
    if args.key != None:
      pub_key_dict = util.import_public_keys_from_files_as_dict(args.key,
          args.key_type)

    # ... or from gpg keyring
    elif args.gpg != None: # pragma: no branch
      pub_key_dict = util.import_gpg_public_keys_from_keyring_as_dict(
          args.gpg, args.gpg_home)


    for keyid, verification_key in six.iteritems(pub_key_dict):
      metadata.verify_signature(verification_key)
      log.info("Signature verification passed for keyid '{}'"
          .format(keyid))

    sys.exit(0)

  except exceptions.SignatureVerificationError as e:
    log.error("Signature verification failed: {}".format(e))
    sys.exit(1)

  except Exception as e:
    log.error("The following error occurred while verifying signatures: "
        "{}".format(e))
    sys.exit(2)


def _load_metadata(file_path):
  """
  <Purpose>
    Loads Metablock (link or layout metadata) file from disk

  <Arguments>
    file_path:
            path to link or layout metadata file

  <Exceptions>
    SystemExit(2) if any exception occurs

  <Returns>
    in-toto Metablock object (contains Link or Layout object)

  """
  try:
    return Metablock.load(file_path)

  except Exception as e:
    log.error("The following error occurred while loading the file '{}': "
        "{}".format(file_path, e))
    sys.exit(2)


def main():
  """Parse arguments, load link or layout metadata file and either sign
  metadata file or verify its signatures. """

  parser = argparse.ArgumentParser(
      formatter_class=argparse.RawDescriptionHelpFormatter,
      description="""
Provides command line interface to sign in-toto link or layout metadata or
verify its signatures, with options to:

  * replace (default) or add signature(s):
    + layout metadata can be signed by multiple keys at once,
    + link metadata can only be signed by one key at a time.

  * write signed metadata to a specified path. If no output path is specified,
    + layout metadata is written to the path of the input file,
    + link metadata is written to '<name>.<keyid prefix>.link'.

  * verify signatures

Returns nonzero value on failure and zero otherwise.""")

  parser.epilog = """
examples:
  Append two signatures to 'unsigned.layout' file and write to 'root.layout'.

      {prog} -f unsigned.layout -k priv_key1 priv_key2 -o root.layout -a


  Replace signature in link file. And write to default filename, i.e.
  'package.<priv_key's keyid prefix>.link'.

      {prog} -f package.2f89b927.link -k priv_key


  Verify layout signed with 3 keys.

      {prog} -f root.layout -k pub_key0 pub_key1 pub_key2 --verify


  Sign layout with default gpg key in default gpg keyring.

      {prog} -f root.layout --gpg


  Verify layout with a gpg key identified by keyid '...439F3C2'.

      {prog} -f root.layout --verify \\
      --gpg 3BF8135765A07E21BD12BF89A5627F6BF439F3C2

""".format(prog=parser.prog)


  named_args = parser.add_argument_group("required named arguments")

  named_args.add_argument("-f", "--file", type=str, required=True,
      metavar="<path>", help=(
        "Path to link or layout file to be signed or verified."))

  parser.add_argument("-k", "--key", nargs="+", metavar="<path>", help=(
      "Path(s) to PEM formatted key file(s), used to sign the passed link or"
      " layout metadata or to verify its signatures."))

  parser.add_argument("-t", "--key-type", dest="key_type",
      type=str, choices=in_toto.util.SUPPORTED_KEY_TYPES,
      nargs="+", help=(
      "Specify the key-type of the keys specified by the '--key'"
      " option. Number of values should be the same as the number of keys"
      " specified by the '--key' option. If '--key-type' is not passed,"
      " default key_type of all keys is assumed to be \"rsa\"."))

  parser.add_argument("-g", "--gpg", nargs="*", metavar="<id>", help=(
      "GPG keyid used to sign the passed link or layout metadata or to verify"
      " its signatures. If passed without keyid, the default GPG key is"
      " used."))

  parser.add_argument("--gpg-home", dest="gpg_home", type=str,
      metavar="<path>", help=(
      "Path to GPG keyring to load GPG key identified by '--gpg' option.  If"
      " '--gpg-home' is not passed, the default GPG keyring is used."))

  # Only when signing
  parser.add_argument("-o", "--output", type=str, metavar="<path>",
      help=(
      "Path to store metadata file to be signed. If not passed, layout"
      " metadata is written to the path of the input file and link metadata is"
      " written to '<step name>.<keyid prefix>.link'"))

  # Only when signing
  parser.add_argument("-a", "--append", action="store_true",
      help=(
      "If passed, signatures are added rather than replacing existing"
      " signatures. This option is only availabe for layout metdata."))

  parser.add_argument("--verify", action="store_true",
      help="Verify signature(s) of passed link or layout metadata.")

  verbosity_args = parser.add_mutually_exclusive_group(required=False)
  verbosity_args.add_argument("-v", "--verbose", dest="verbose",
      help="Verbose execution.", action="store_true")

  verbosity_args.add_argument("-q", "--quiet", dest="quiet",
      help="Suppress all output.", action="store_true")

  args = parser.parse_args()

  log.setLevelVerboseOrQuiet(args.verbose, args.quiet)

  # Additional argparse sanitization
  # NOTE: This tool is starting to have many inter-dependent argument
  # restrictions. Maybe we should make it less sophisticated at some point.
  if args.verify and (args.append or args.output):
    parser.print_help()
    parser.error("conflicting arguments: don't specify any of"
        " 'append' or 'output' when verifying signatures")

  # Regular signing and GPG signing are mutually exclusive
  if (args.key == None) == (args.gpg == None):
    parser.print_help()
    parser.error("wrong arguments: specify either `--key PATH [PATH ...]`"
      " or `--gpg [KEYID [KEYID ...]]`")

  # For gpg verification we must specify a keyid (no default key is loaded)
  if args.verify and args.gpg != None and len(args.gpg) < 1:
    parser.print_help()
    parser.error("missing arguments: specify at least one keyid for GPG"
      " signature verification (`--gpg KEYID ...`)")

  metadata = _load_metadata(args.file)

  # Specific command line argument restrictions if we deal with links
  if metadata.type_ == "link":
    # Above we check that it's either `--key ...` or `--gpg ...`
    # Here we check that it is not more than one in each case when dealing
    # with links
    link_error_message = ("Link metadata is associated with a"
        " single functionary and is usually namespaced accordingly:"
        " '<name>.<keyid>.link'.")

    if ((args.key != None and len(args.key) > 1) or
        (args.gpg != None and len(args.gpg) > 1)):
      parser.print_help()
      parser.error("too many arguments: {} Hence signing Link metadata"
          " with multiple keys is not allowed.".format(link_error_message))

    if args.append:
      parser.print_help()
      parser.error("wrong arguments: {}. Hence adding signatures to"
          " existing signatures on Link metadata is not allowed."
          .format(link_error_message))


  if args.verify:
    _verify_metadata(metadata, args)

  else:
    _sign_and_dump_metadata(metadata, args)


if __name__ == "__main__":
  main()
