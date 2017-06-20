"""
<Program Name>
  in_toto_sign.py

<Author>
  Sachit Malik <i.sachitmalik@gmail.com>

<Started>
  June 13, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  A CLI tool for adding, replacing, verifying signatures in link
  metadata files. It takes the following inputs - path to the signable
  object, and path to the key file. Also there are two optional inputs
  based on which it decides whether to sign the file with the replacement
  of the existing signature, or sign it but without replacement and then
  appends the new signature in the file. Further in each of the two cases,
  depending on the arguments it then dumps the file either by infixing
  the keyID i.e. <filename>.<8-initial-characters-from-the-keyID>.link
  or simply <filename>.link

  General Usage:
  python in_toto_sign.py --key <path/to/key> <sign/verify> [-r] [-i]
    <path/to/link/file>

  Example Usage:
  Suppose Bob wants to sign a file called package.link, and also while signing,
  he wants to replace all the existing signatures, and then dump the file
  by infixing the keyID in it. Then his command would be-

  python in_toto_sign.py --key /bob/mykeys/bob_pvt_key
    sign -r -i  /bob/software/in-toto/test/package.link

"""
import os
import sys
import argparse
import in_toto.log
import in_toto.util
from in_toto.models.common import Signable as signable_object
from in_toto.models.link import Link as link_import
import securesystemslib.exceptions
import securesystemslib.keys
import securesystemslib.formats


def add_sign(link, key):
  """
    <Purpose>
      Signs the given link file with the corresponding key,
      adds the signature to the file, and then returns, the
      link file as an object.

    <Arguments>
      link - path to the signable link file
      key - the key to be used for signing

    <Exceptions>
      None

    <Returns>
      An object containing the contents of the link file after
      adding the signature

  """
  # Reading the file from the given link and making an object
  signable_object = link_import.read_from_file(link)

  # Import the rsa key from the file specified in the filepath
  rsa_key = in_toto.util.prompt_import_rsa_key_from_file(key)

  # Checking if the given key follows the format
  securesystemslib.formats.KEY_SCHEMA.check_match(rsa_key)

  signable_object.sign(rsa_key)

  '''
  '# Create the signature using the key, and the link file
  signature = securesystemslib.keys.create_signature(rsa_key,
                  signable_object.payload)

  # Append the signature into the file
  signable_object.signatures.append(signature)
  '''

  return signable_object


def replace_sig(link, key):
    """
    <Purpose>
      Replaces all the existing signature with the new signature,
      signs the file, and then returns the link file as an object.

    <Arguments>
      link - path to the key file
      key - the key to be used for signing

    <Exceptions>
      None

    <Returns>
      An object containing the contents of the link file after
      adding the signature which replaces the old signatures
    """

    # Reading the link file and making an object
    signable_object = link_import.read_from_file(link)

    # Import rsa key from the filepath
    rsa_key = in_toto.util.prompt_import_rsa_key_from_file(key)

    # Check if the key corresponds to the correct format
    securesystemslib.formats.KEY_SCHEMA.check_match(rsa_key)
    # core working
    # signature = securesystemslib.keys.create_signature(rsa_key,
    # signable_object.payload)
    signable_object.signatures = []
    signable_object.sign(rsa_key)

    return signable_object


def verify_sign(link, key_pub):
    """
    <Purpose>
      Verifies the signature field in the link file, given a public key

    <Arguments>
      link - path to the link file
      key_pub - public key to be used to verification

    <Exceptions>
      Raises SignatureVerificationError
        - 'Invalid Signature' : when the verification fails
        - 'Signature Key Not Found' : when KeyError occurs
        - 'No Signatures Found' - when no signature exists

    <Returns>
      Boolean True when the verification is success
    """

    signable_object = link_import.read_from_file(link)
    link_key_dict = in_toto.util.import_rsa_public_keys_from_files_as_dict(
      [key_pub])
    signable_object.verify_signatures(link_key_dict)

def parse_args():
    """
    <Purpose>
      A function which parses the user supplied arguments.

    <Arguments>
      None

    <Exceptions>
      None

    <Returns>
      Parsed arguments (args object)
    """
    parser = argparse.ArgumentParser(
        description="in-toto-sign : Signs link file with/without replacement, "
                    "and dumps with/without infixing the keyID in the "
                    "filename")

    lpad = (len(parser.prog) + 1) * " "

    parser.usage = ("\n"
                    "(sign | verify) --key <filepath>\n{0}"
                    "[--replace-sig]\n{0}"
                    "[--infix]\n{0}"
                    "[--verbose]\n{0}"
                    "<path/to/signable>\n\n"
                    .format(lpad))

    in_toto_args = parser.add_argument_group("in-toto-sign options")

    in_toto_args.add_argument("operator", type=str, choices=['sign', 'verify'],
                              help="Sign or Verify")

    in_toto_args.add_argument("-k", "--key", type=str, required=True,
                              help="Path to the key ")

    in_toto_args.add_argument("-r", "--replace-sig", action="store_true",
                              help="Replace all the old signatures, sign "
                                   "with the given key, and add the new "
                                   "signature in file")

    in_toto_args.add_argument("-i", "--infix", action="store_true",
                              help="Infix keyID in the filename while "
                                   "dumping, when -i the file will be dumped as"
                                   "original.<keyID>.link, else original.link")

    in_toto_args.add_argument("-v", "--verbose", dest="verbose",
                              help="Verbose execution.", default=False,
                              action="store_true")

    in_toto_args.add_argument("signablepath", type=str,
                              help="path to the signable file")

    args = parser.parse_args()
    args.operator = args.operator.lower()

    return args


def main():
    """
    First calls parse_args to parse the arguments, and then calls either
    add_sign or add_replace depending upon the arguments. Based on the
    arguments it then dumps the corresponding file.

    """
    args = parse_args()
    rsa_key = in_toto.util.import_rsa_key_from_file(args.key)

    if args.verbose:
      log.logging.getLogger.setLevel(log.logging.INFO)

    try:
      if args.operator == 'sign':
        if args.replace-sig:
          signable_object = replace_sig(args.signablepath, args.key)

        else:
          signable_object = add_sign(args.signablepath, args.key)

        if args.infix:
          signable_object.dump(key=rsa_key)
          sys.exit(0)

        else:
          signable_object.dump()
          sys.exit(0)

      else:
          verify_sign(args.signablepath, args.key)

    except Exception as e:
      print('The following error occurred', e)
      sys.exit(1)

if __name__ == "__main__":
    main()
