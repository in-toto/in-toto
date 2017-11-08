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
  or verify its signatures.

  Provides options to,
    - replace (default) or add signature(s):
        - Layout metadata can be signed by multiple keys at once,
        - Link metadata can only be signed by one key at a time

    - write signed metadata to a specified path:
      if no output path is specified,
        - layout metadata is written to the input file,
        - link metadata is written to:
         "<step name>.<short signing key id>.link"

    - verify signatures




  Usage:
  ```
  in-toto-sign [-h] -f FILE -k KEY [KEY ...] [-o OUTPUT] [-a] [-v]
               [--verify]
  ```

  Examples:
  ```
  # Append two signatures to layout file and write to passed path
  in-toto-sign -f unsigned.layout -k priv_key1 priv_key2 -o root.layout -a

  # Re-sign specified link
  # Since -o is not specified, write to default output filename, using the
  # short id for priv_key as a filename infix (in place of "2f89b927")
  in-toto-sign -f package.2f89b927.link -k priv_key

  # Verify Layout signed with three keys
  in-toto-sign -f root.layout -k pub_key0 pub_key1 pub_key2 --verify

  ```

"""
import os
import sys
import json
import argparse
import in_toto.user_settings
from in_toto import log, exceptions, util
from in_toto.models.link import FILENAME_FORMAT
from in_toto.models.metadata import Metablock

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

    for key_path in args.key:
      key = util.prompt_import_rsa_key_from_file(key_path)
      metadata.sign(key)

      # Only relevant when signing Link metadata, where there is only one key
      keyid = key["keyid"]

    if args.output:
      out_path = args.output

    elif metadata._type == "link":
      out_path = FILENAME_FORMAT.format(step_name=metadata.signed.name,
          keyid=keyid)

    elif metadata._type == "layout":
      out_path = args.file

    log.info("Dumping {0} to '{1}'...".format(metadata._type,
        out_path))

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
    pub_key_dict = util.import_rsa_public_keys_from_files_as_dict(
        args.key)

    metadata.verify_signatures(pub_key_dict)
    log.pass_verification("Signature verification passed")
    sys.exit(0)

  except exceptions.SignatureVerificationError as e:
    log.fail_verification("Signature verification failed: {}".format(e))
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
    description="Sign in-toto Link or Layout metadata (or verify signatures)")

  parser.add_argument("-f", "--file", type=str, required=True,
      help="read metadata file from passed path (required)")

  parser.add_argument("-k", "--key", nargs="+", type=str, required=True,
      help="key path(s) used to sign or verify metadata (at least - "
      " in case of signing Link metadata only - one key required)")

  # Only when signing
  parser.add_argument("-o", "--output", type=str,
      help="store signed metadata file to passed path, if not passed Layout"
      " metadata is written to the input file and Link metadata is written to"
      " '<step name>.<short signing key id>.link'")

  # Only when signing
  parser.add_argument("-a", "--append", action="store_true",
      help="append to existing signatures (only available for Layout"
      " metadata")

  parser.add_argument("-v", "--verbose", dest="verbose", action="store_true")

  parser.add_argument("--verify", action="store_true",
      help="verify signatures")

  args = parser.parse_args()

  if args.verbose:
    log.logging.getLogger().setLevel(log.logging.INFO)

  # Override defaults in settings.py with environment variables and RCfiles
  in_toto.user_settings.set_settings()

  if args.verify and (args.append or args.output):
    parser.print_help()
    parser.exit(2, "conflicting arguments: don't specify any of"
        " 'append' or 'output' when verifying signatures")

  metadata = _load_metadata(args.file)

  if metadata._type == "link":
    if len(args.key) > 1:
      parser.print_help()
      parser.exit(2, "wrong arguments: Link metadata can only be signed by"
          " one key")

    if args.append:
      parser.print_help()
      parser.exit(2, "wrong arguments: Link metadata signatures can not be"
          " appended to existing signatures")

  if args.verify:
    _verify_metadata(metadata, args)

  else:
    _sign_and_dump_metadata(metadata, args)


if __name__ == "__main__":
  main()
