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

"""
import os
import sys
import argparse
import in_toto.log
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
      None

    """
    # reading the file from the given link and making an object
    signable_object = link_import.read_from_file(link)

    # checking if the given key follows the format
    securesystemslib.formats.KEY_SCHEMA.check_match(key)

    # create the signature using the key, and the link file
    signature = securesystemslib.keys.create_signature(key, signable_object.payload)

    # append the signature into the file
    signable_object.signatures.append(signature)

    # dump the file with link name + '.link'
    signable_object.dump()


def replace_old_sign(link, key):
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
      None

    """
    # reading the link file and making an object
    signable_object = link_import.read_from_file(link)

    # check if the key corresponds to the correct format
    securesystemslib.formats.KEY_SCHEMA.check_match(key)

    # core working
    signature = securesystemslib.keys.create_signature(key, signable_object.payload)
    signable_object.signatures = []
    signable_object.signatures["keyid"] = key
    signable_object.signatures["sig"] = signature
    signable_object.signatures["method"] = "RSASSA-PSS"

    # dump the file with link name + '.link'
    signable_object.dump()
    os.remove(link)


def add_infix(link, key):
    """
    <Purpose>
      Infixes the keyID in the filename

    <Arguments>
      link - the path to the link file
      key - the key whose keyID needs to be infixed in the filename

    <Exceptions>
      None

    <Returns>
      None

    """

    signable_object = link_import.read_from_file(link)

    # securesystemslib.formats.KEY_SCHEMA.check_match(key)
    # signature = securesystemslib.keys.create_signature(key, signable_object.payload)

    signable_object.dump(key=key)
    os.remove(link)


def verify_sign(link, key_pub):
    """
    <Purpose>
      Verifies the signature field in the link file, given a public key

    <Arguments>
      link - path to the link file
      key_pub - public key to be used to verification

    <Exceptions>
      None

    <Returns>
      None

    """

    link_key_dict = in_toto.util.import_rsa_public_keys_from_files_as_dict(
        key_pub)
    link.verify_link_signatures(link_key_dict)


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
                    "[--replace-all-old-signatures]\n{0}"
                    "[--add-keyid-infix-to-filename]\n{0}"
                    "<path/to/signable>"
                    "[--verbose]\n\n"
                    .format(lpad))

    in_toto_args = parser.add_argument_group("in-toto-sign options")

    in_toto_args.add_argument("-k", "--key", type=str, required=True,
                              help="Path to private key to sign link metadata (PEM)")

    in_toto_args.add_argument("operator", type=str,
                              help="sign or verify")

    in_toto_args.add_argument("-r", "--replaceall", required=False,
                              type=str, help="Whether to replace"
                                             "all the old signatures or not")

    in_toto_args.add_argument("-i", "--keyidinfix", required=False,
                              type=str, help="whether to add"
                                             "key id infix in the file name")

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

    if args.verbose:
        log.logging.getLogger.setLevel(log.logging.INFO)

    if args.operator == 'sign':

        try:

            if not args.replaceall:

                if not args.keyidinfix:
                    add_sign(args.signablepath, args.key)
                    sys.exit(0)

                else:
                    add_sign(args.signablepath, args.key)
                    add_infix(args.signablepath, args.key)
                    sys.exit(0)

            else:

                if not args.keyidinfix:
                    replace_old_sign(args.signablepath, args.key)
                    sys.exit(0)

                else:
                    replace_old_sign(args.signablepath, args.key)
                    add_infix(args.signablepath, args.key)
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

    else:
        raise Exception('Invalid Operator Supplied')
        sys.exit(4)


if __name__ == "__main__":
    main()
