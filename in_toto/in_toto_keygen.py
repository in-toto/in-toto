#!/usr/bin/env python
"""
<Program Name>
  in_toto_keygen.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>
  Sachit Malik <i.sachitmalik@gmail.com>

<Started>
  June 28, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  A CLI tool for creating key files, and dumping them with <filename>,
  <filename>.pub for private and public keys respectively. It also takes an
  integer as an input, which specifies the length of the RSA key to be
  generated. By default it is set as 3072.

<Return Codes>
  2 if an exception occurred during argument parsing
  1 if an exception occurred
  0 if no exception occurred

"""
import sys
import argparse
import logging

from in_toto.common_args import title_case_action_groups
from in_toto import (
    __version__, SUPPORTED_KEY_TYPES, KEY_TYPE_RSA, KEY_TYPE_ED25519)
from securesystemslib import interface

# Command line interfaces should use in_toto base logger (c.f. in_toto.log)
LOG = logging.getLogger("in_toto")


def create_parser():
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
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="in-toto-keygen is a tool to generate, optionally encrypt, and"
                " write cryptographic keys to disk. These keys may be used"
                " with other in-toto tooling to e.g. sign or verify link or"
                " layout metadata.")

  parser.epilog = """EXAMPLE USAGE

Generate RSA key pair of size 2048 bits, prompt for a password to encrypt
the private key, and write 'alice' (private encrypted) and 'alice.pub' (public)
as PEM-formatted key files to the current working directory.

  in-toto-keygen -p -t rsa -b 2048 alice


Generate unencrypted ed25519 key pair and write 'bob' (private) and 'bob.pub'
(public) as securesystemslib/json-formatted key files to the current working
directory.

  in-toto-keygen -t ed25519 bob


"""

  parser.add_argument("-p", "--prompt", action="store_true",
                            help="prompts for a password used to encrypt the"
                            " private key before storing it")

  parser.add_argument("-t", "--type", type=str,
                            choices=SUPPORTED_KEY_TYPES,
                            default=KEY_TYPE_RSA,
                            help="type of the key to be generated. '{rsa}'"
                            " keys are written in a 'PEM' format and"
                            " '{ed25519}' in a custom 'securesystemslib/json'"
                            " format. Default is '{rsa}'.".format(
                            rsa=KEY_TYPE_RSA, ed25519=KEY_TYPE_ED25519))


  parser.add_argument("name", type=str, metavar="<filename>",
                            help="filename for the resulting key files, which"
                            " are written to '<filename>' (private key) and"
                            " '<filename>.pub' (public key).")

  parser.add_argument("-b", "--bits", default=3072, type=int, metavar="<bits>",
                            help="key size, or key length, of the RSA key")

  parser.add_argument('--version', action='version',
                      version='{} {}'.format(parser.prog, __version__))

  title_case_action_groups(parser)

  return parser



def main():
  """
  First calls parse_args to parse the arguments, and then calls either
  _generate_and_write_rsa_keypair or _generate_and_write_ed25519_keypair
  depending upon the arguments. It then dumps the corresponding key files as:
  <filename> and <filename>.pub (Private key and Public key respectively)
  """
  parser = create_parser()
  args = parser.parse_args()

  try:
    if args.type == KEY_TYPE_RSA:
      interface._generate_and_write_rsa_keypair( # pylint: disable=protected-access
          filepath=args.name, bits=args.bits, prompt=args.prompt)
    elif args.type == KEY_TYPE_ED25519:
      interface._generate_and_write_ed25519_keypair( # pylint: disable=protected-access
          filepath=args.name, prompt=args.prompt)
    else:  # pragma: no cover
      LOG.error(
          "(in-toto-keygen) Unsupported keytype: {0}".format(str(args.type)))
      sys.exit(1)
    sys.exit(0)

  except Exception as e:
    LOG.error("(in-toto-keygen) {0}: {1}".format(type(e).__name__, e))
    sys.exit(1)

if __name__ == "__main__":
  main()
