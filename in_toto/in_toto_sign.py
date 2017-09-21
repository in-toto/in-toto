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
  or simply <filename>.link. Note that in case of signing by multiple key
  files, when -i is specified, file is dumped by the keyID of the last key
  supplied in the arguments.

  General Usage:
  python in_toto_sign.py [sign | verify] <path/to/link/file> [-r] [-i] --keys
  <path/to/key/file(s)>

  Example Usage:
  Suppose Bob wants to sign a file called package.link, and also while signing,
  he wants to replace all the existing signatures, and then dump the file
  by infixing the keyID in it. Then his command would be-

  python in_toto_sign.py sign /bob/software/in-toto/test/package.link -r -i
  --keys /bob/mykeys/bob_pvt_key

"""
import os
import json
import sys
import argparse
import in_toto.util
from in_toto import log
from in_toto import exceptions
from in_toto.models.common import Signable as signable_object
from in_toto.models.layout import Layout as layout_import
from in_toto.models.link import Link as link_import
from in_toto.models.link import FILENAME_FORMAT as FILENAME_FORMAT_IMPORT
import securesystemslib.exceptions
import securesystemslib.keys
import securesystemslib.formats


def add_sign(file_path, key_dict):
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
  signable_object = check_file_type_and_return_object(file_path)

  for key in key_dict:
    # Import the rsa key from the file specified in the filepath
    rsa_key = in_toto.util.prompt_import_rsa_key_from_file(key)

    # Checking if the given key follows the format
    securesystemslib.formats.KEY_SCHEMA.check_match(rsa_key)

    signable_object.sign(rsa_key)

  return signable_object


def replace_sign(file_path, key_dict):
  """
  <Purpose>
    Replaces all the existing signature with the new signature,
    signs the file, and then returns the link file as an object.

  <Arguments>
    link - path to the key file
    key - the key/keys to be used for signing

  <Exceptions>
    None

  <Returns>
    An object containing the contents of the link file after
    adding the signature which replaces the old signatures
  """
  signable_object = check_file_type_and_return_object(file_path)

  # Remove all the existing signatures
  signable_object.signatures = []

  for key in key_dict:
    # Import rsa key from the filepath
    rsa_key = in_toto.util.prompt_import_rsa_key_from_file(key)

    # Check if the key corresponds to the correct format
    securesystemslib.formats.KEY_SCHEMA.check_match(rsa_key)

    # Sign the object
    signable_object.sign(rsa_key)

  return signable_object


def verify_sign(file_path, key_pub):
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
    None
  """
  signable_object = check_file_type_and_return_object(file_path)
  key_pub_dict = in_toto.util.import_rsa_public_keys_from_files_as_dict(
      key_pub)
  signable_object.verify_signatures(key_pub_dict)


def check_file_type_and_return_object(file_path):
  """
  <Purpose>
    Checks the file type of the file at file_path and returns a signable
    object if the file is a link or a layout

  <Arguments>
    file_path - path to the file

  <Exceptions>
    Raises LinkNotFoundError when a file other than link or layout is
    encountered.

  <Returns>
    A signable object
  """
  with open(file_path,'r') as fp:
    file_object = json.load(fp)

    if 'signed' not in file_object:
        raise TypeError("This file is probably not in-toto metadata ;[")

    if file_object['signed'].get("_type") == "link":
      signable_object = link_import.read(file_object)
      return signable_object

    elif file_object['signed'].get("_type") == "layout":
      signable_object = layout_import.read(file_object)
      return signable_object

    else:
      raise exceptions.LinkNotFoundError("Invalid format.'{0}' is not a "
        "valid in-toto 'Link' or 'Layout' metadata file.".format(file_path))


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
    description="in-toto-sign : Signs(single/multiple signing) link file "
                "with/without replacement of the existing signatures and dumps"
                " with/without infixing the keyID in the (user "
                "provided/source) file name")

  subparsers = parser.add_subparsers(help='in-toto sign/verify subparsers',
                                     dest='subparser_name')

  sign_parser = subparsers.add_parser('sign', help='Sign the link/layout '
                                      'file.')

  sign_parser.add_argument("signablepath", type=str,
                            help="path to the signable file")

  sign_parser.add_argument("-r", "--replace-sig", action="store_true",
                            help="Replace all the old signatures, sign "
                                 "with the given key, and add the new "
                                 "signature in file")

  sign_parser.add_argument("-i", "--infix", action="store_true",
                            help="Infix keyID in the filename while "
                                 "dumping, when -i the file will be dumped "
                                 "as original.<keyID>.link/layout, "
                                 "else original.link/layout")

  sign_parser.add_argument("-v", "--verbose", dest="verbose",
                            help="Verbose execution.", default=False,
                            action="store_true")

  sign_parser.add_argument("-d", "--destination", type=str, help="Filepath "
                           "to which the output file should be dumped")

  sign_parser.add_argument("-k", "--keys", nargs="+", type=str, required=True,
                            help="Path to the key file/files")

  verify_parser = subparsers.add_parser('verify', help='Verify the '
                                        'link/layout file.')

  verify_parser.add_argument("signablepath", type=str,
                            help="path to the signable file")

  verify_parser.add_argument("-v", "--verbose", dest="verbose",
                            help="Verbose execution.", default=False,
                            action="store_true")

  verify_parser.add_argument("-k", "--keys", nargs="+", type=str,
                            required=True, help="Path to the key file/files")


  args = parser.parse_args()
  return args

def main():
  """
  First calls parse_args to parse the arguments, and then calls either
  add_sign or add_replace depending upon the arguments. Based on the
  arguments it then dumps the corresponding file.
  """
  args = parse_args()

  if args.verbose:
    log.logging.getLogger().setLevel(log.logging.INFO)

  if args.subparser_name == 'sign':
    try:
      if args.destination and args.infix:
        log.error('Please specify one and only one out of infix and '
                  'destination!')
        sys.exit(1)

      if args.replace_sig:
        signable_object = replace_sign(args.signablepath, args.keys)
      else:
        signable_object = add_sign(args.signablepath, args.keys)

      if signable_object._type == 'layout':
        if args.infix:
          log.warn('Ignoring option --infix for layouts...')

        if args.destination:
          path = args.destination

        else:
          path = args.signablepath


      if signable_object._type == 'link':
        if args.destination:
          path = args.destination

        elif args.infix:
          rsa_key = in_toto.util.import_rsa_key_from_file(args.keys[-1])
          path = FILENAME_FORMAT_IMPORT.format(step_name=signable_object.name,
                  keyid=rsa_key["keyid"])
          if len(args.keys) > 1:
            log.warn('Using last key in the list of passed keys for infix...')

        else:
          path = args.signablepath

      log.info("Dumping {0} to '{1}'...".format(signable_object._type.lower(),
          path))

      signable_object.dump(path)
      sys.exit(0)

    except Exception as e:
      log.error("Unable to sign. Error Occured - {}".format(e))
      sys.exit(1)

  elif args.subparser_name == 'verify':
    try:
      verify_sign(args.signablepath, args.keys)
      log.pass_verification('Successfully verified.')
      sys.exit(0)

    except exceptions.SignatureVerificationError as e:
      log.fail_verification('Verification Failed.' + str(e))
      sys.exit(1)

    except Exception as e:
      log.error("The following error occured while verification - "
                "'{}'".format(e))
      sys.exit(2)


if __name__ == "__main__":
    main()
