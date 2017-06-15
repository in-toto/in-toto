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
  metadata files.
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
    adds the signature to the file, and dumps it using the
    link name + '.link'-suffix

    <Arguments>
      link - path to the signable link file
      key - the key to be used for signing

    <Exceptions>
      None

    <Returns>
      An object containing the contents of the link file after
      adding the signature

    """
    # reading the file from the given link and making an object
    signable_object = link_import.read_from_file(link)

    rsa_key = in_toto.util.import_rsa_key_from_file(key)

    # checking if the given key follows the format
    securesystemslib.formats.KEY_SCHEMA.check_match(rsa_key)

    # create the signature using the key, and the link file
    signature = securesystemslib.keys.create_signature(rsa_key, signable_object.payload)

    # append the signature into the file
    signable_object.signatures.append(signature)

    return signable_object


def add_replace(link, key):
    """
    <Purpose>
      Replaces all the exisiting signature with the new signature,
      signs the file, and dumps it with link name + '.link'

    <Arguments>
      link - path to the key file
      key - the key to be used for signing

    <Exceptions>
      None

    <Returns>
      An object containing the contents of the link file after
      adding the signature which replaces the old signatures
    """

    # reading the link file and making an object
    signable_object = link_import.read_from_file(link)

    # import rsa key from the filepath
    rsa_key = in_toto.util.import_rsa_key_from_file(key)

    # check if the key corresponds to the correct format
    securesystemslib.formats.KEY_SCHEMA.check_match(rsa_key)

    # core working
    signature = securesystemslib.keys.create_signature(rsa_key, signable_object.payload)
    signable_object.signatures = []
    signable_object.signatures.append(signature)

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

    return True


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
        description="in-toto-sign : Signs etc etc")

    lpad = (len(parser.prog) + 1) * " "

    parser.usage = ("\n"
                    "--key <signing key> | <verifying key>\n{0}"
                    "<sign | verify>\n{0}"
                    "[--replaceall]\n{0}"
                    "[--infixkeyid]\n{0}"
                    "<path/to/signable>"
                    "[--verbose]\n\n"
                    .format(lpad))

    in_toto_args = parser.add_argument_group("in-toto-sign options")

    in_toto_args.add_argument("-k", "--key", type=str, required=True,
                              help="Path to private key to sign link metadata (PEM)")

    in_toto_args.add_argument("operator", type=str, choices=['sign', 'verify'],
                              help="sign or verify")

    in_toto_args.add_argument("-r", "--replaceall", required= False,
                              type=str, help="Whether to replace"
                              "all the old signatures or not")

    in_toto_args.add_argument("-i", "--infixkeyid", required= False,
                              type=str, help="whether to"
                             "infix keyid in the file name")

    in_toto_args.add_argument("signablepath", type=str,
                              help="path to the signable file")

    in_toto_args.add_argument("-v", "--verbose", dest="verbose",
                              help="Verbose execution.", default=False,
                              action="store_true")

    args = parser.parse_args()
    args.operator = args.operator.lower()

    return args


def main():
    """

    """
    args = parse_args()
    rsa_key = in_toto.util.import_rsa_key_from_file(args.key)

    if args.verbose:
        log.logging.getLogger.setLevel(log.logging.INFO)

    if args.operator == 'sign':

      try:
        if not args.replaceall:

          if not args.infixkeyid:
            signable_object = add_sign(args.signablepath, args.key)
            signable_object.dump()
            sys.exit(0)

          else:
            signable_object = add_sign(args.signablepath, args.key)
            signable_object.dump(key = rsa_key)
            sys.exit(0)

        else:

          if not args.infixkeyid:
            signable_object = add_replace(args.signablepath, args.key)
            signable_object.dump()
            sys.exit(0)

          else:
            signable_object = add_replace(args.signablepath, args.key)
            signable_object.dump(key = rsa_key)
            sys.exit(0)

      except Exception as e:
        print('The following error occured while signing', e)
        sys.exit(2)

    elif args.operator == 'verify':

      try:
        if verify_sign(args.signablepath, args.key):
          sys.exit(0)
        else:
          sys.exit(1)

      except Exception as e:
        print('The following error occured while verification', e)
        sys.exit(3)



if __name__ == "__main__":
    main()
