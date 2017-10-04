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
  Provides command line interface to sign in-toto Link or Layout metadata
  or verify its signatures.

  The tool provides options to
    - add or replace signatures,
    - write the signed file to a specified path,
    - write the signed file to a path consisting of
      the value from the metadata's `name` field, the first 8 characters
      of the signing key's id as infix and '.link' as extension,
      e.g.:  "package.c1ae1e51.link"
      Note:
        The naming scheme is used to distinguish Link files of steps that are
        required to be carried out by a threshold of functionaries.
        This option is only available for Link metadata.
        If multiple keys are passed for signing, the short key id of the last
        key in the arguments list is used as infix.

    - verify signatures


  Usage:
  ```
  in-toto-sign [-h] -f FILE -k KEYS [KEYS ...] [-o OUTPUT] [-x] [-r] [-v]
               [--verify]
  ```

  Examples:
  ```
  # Sign Layout with two keys and write to specified path
  in-toto-sign -f unsigned.layout -k priv_key1 priv_key2 -o root.layout

  # Sign Link and use passed key's short id as filename infix
  in-toto-sign -f package.c1ae1e51.link -k priv_key -x

  # Verify Layout signed with two keys
  in-toto-sign -f root.layout -k pub_key1 pub_key2 --verify

  ```

"""
import os
import sys
import json
import argparse
from in_toto import log, exceptions, util
from in_toto.models.layout import Layout
from in_toto.models.link import Link, FILENAME_FORMAT

def _sign_and_dump_metadata(metadata, args):
  """
  <Purpose>
    Internal method to sign Link or Layout metadata and dump it to disk.

  <Arguments>
    metadata:
            Link or Layout object
    args:
            see argparser

  <Exceptions>
    SystemExit(0) if signing is successful
    SystemExit(2) if any exception occurs

  """

  try:
    if args.replace:
      metadata.signatures = []

    for key_path in args.keys:
      key = util.prompt_import_rsa_key_from_file(key_path)
      metadata.sign(key)
      # Only keeping  in the passed list will be used as infix
      keyid = key["keyid"]

    out_path = args.file

    if args.infix:
      if len(args.keys) > 1:
        log.warn("Using last key in the list of passed keys for infix...")

      out_path = FILENAME_FORMAT.format(step_name=metadata.name,
          keyid=keyid)

    if args.output:
      out_path = args.output

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
    Internal method to verify Link or Layout signatures.

  <Arguments>
    metadata:
            Link or Layout object
    args:
            see argparser

  <Exceptions>
    SystemExit(0) if verification passes
    SystemExit(1) if verification fails
    SystemExit(2) if any exception occurs

  """
  try:
    pub_key_dict = util.import_rsa_public_keys_from_files_as_dict(
        args.keys)

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
    Loads Link or Layout file from disk

  <Arguments>
    file_path:
            path to Link or Layout file

  <Exceptions>
    SystemExit(2) if any exception occurs

  <Returns>
    in-toto Link or Layout object

  """
  try:
    with open(file_path, "r") as fp:
      file_object = json.load(fp)

    if file_object.get("signed", {}).get("_type") == "link":
      return Link.read(file_object)

    elif file_object.get("signed", {}).get("_type") == "layout":
      return Layout.read(file_object)

    else:
      raise Exception("Not a valid in-toto 'Link' or 'Layout'"
          " metadata file")

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

  parser.add_argument("-k", "--keys", nargs="+", type=str, required=True,
      help="path(s) to key file(s) used for signing or signature verification"
      " (required)")

  # Only when signing
  parser.add_argument("-o", "--output", type=str,
      help="store signed metadata file to passed path")

  # Only when signing Link files
  parser.add_argument("-x", "--infix", action="store_true",
      help="write signed file to '<link name>.<infix>.link', where infix is "
      "the short form of the signing key's id (only available for Link "
      "metadata, if multiple keys are passed the last key in the "
      "argument list is used)")

  # Only when signing
  parser.add_argument("-r", "--replace", action="store_true",
      help="replace existing signatures (if not specified signatures are"
      " appended)")

  parser.add_argument("-v", "--verbose", dest="verbose", action="store_true")

  parser.add_argument("--verify", action="store_true",
      help="verify signatures")

  args = parser.parse_args()

  if args.verbose:
    log.logging.getLogger().setLevel(log.logging.INFO)

  if args.infix and args.output:
    parser.print_help()
    parser.exit(2, "conflicting arguments: specify either 'infix' or 'out path'")

  if args.verify and (args.replace or args.infix or args.output):
    parser.print_help()
    parser.exit(2, "conflicting arguments: don't specify any of"
        " 'replace', 'infix' or 'output' when verifying")

  metadata = _load_metadata(args.file)

  if metadata._type == "layout" and args.infix:
    parser.print_help()
    parser.exit(2, "wrong argument: infix option is not available for Layouts")

  if args.verify:
    _verify_metadata(metadata, args)

  else:
    _sign_and_dump_metadata(metadata, args)


if __name__ == "__main__":
  main()
