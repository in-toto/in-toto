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

  General Usage:
  in-toto-keygen [-p] [-t {ed25519, rsa}] [--bits=<bits>] <filename>

  Example Usage:
  Suppose Bob wants to create the rsa keys of size 2048 bits and dump them with
  file name "bob_keys" in the current directory. He also wants to encrypt the
  so created private key with his choice of passphrase. The keys would then be
  created, the private key would be encrypted and dumped as "./bob_keys" and
  public key would be dumped as "./bob_keys.pub". Bob will use the following
  command:

  in-toto-keygen -p -t rsa -b 2048 bob_keys

  in-toto-keygen -p -t ed25519 bob_keys


<Return Codes>
  2 if an exception occurred during argument parsing
  1 if an exception occurred
  0 if no exception occurred

"""
import sys
import argparse
import logging

import in_toto.util

# Command line interfaces should use in_toto base logger (c.f. in_toto.log)
log = logging.getLogger("in_toto")


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
    description="in-toto-keygen : Generates the keys, stores them with the "
                "supplied name (public key as: <name>.pub, private key as: "
                "<name>), additionally prompts for a password when -p is "
                "supplied and encrypts the private key with the same, "
                "before storing")

  in_toto_args = parser.add_argument_group("in-toto-keygen options")

  in_toto_args.add_argument("-p", "--prompt", action="store_true",
                            help="Prompts for a password and encrypts the "
                            "private key with the same before storing")

  in_toto_args.add_argument("-t", "--type", type=str,
                            choices=in_toto.util.SUPPORTED_KEY_TYPES,
                            default=in_toto.util.KEY_TYPE_RSA,
                            help="Type of the key to be generated")

  in_toto_args.add_argument("name", type=str,
                            help="The filename of the resulting key files",
                            metavar="<filename>")

  in_toto_args.add_argument("-b", "--bits", default=3072, type=int,
                            help="The key size, or key length, of the RSA "
                            "key.", metavar="<bits>")

  args = parser.parse_args()

  return args


def main():
  """
  First calls parse_args to parse the arguments, and then calls either
  prompt_generate_and_write_rsa_keypair or generate_and_write_rsa_keypair
  depending upon the arguments. It then dumps the corresponding key files as:
  <filename> and <filename>.pub (Private key and Public key respectively)
  """
  args = parse_args()

  try:
    if args.prompt:
      if args.type == in_toto.util.KEY_TYPE_RSA:
        in_toto.util.prompt_generate_and_write_rsa_keypair(args.name,
                                                           args.bits)
      elif args.type == in_toto.util.KEY_TYPE_ED25519:
        in_toto.util.prompt_generate_and_write_ed25519_keypair(args.name)
      else:  # pragma: no cover
        log.error("(in-toto-keygen) Unsupported keytype: {0}".format(str(args.type)))
        sys.exit(1)
      sys.exit(0)
    else:
      if args.type == in_toto.util.KEY_TYPE_RSA:
        in_toto.util.generate_and_write_rsa_keypair(args.name)
      elif args.type == in_toto.util.KEY_TYPE_ED25519:
        in_toto.util.generate_and_write_ed25519_keypair(args.name)
      else:  # pragma: no cover
        log.error("(in-toto-keygen) Unsupported keytype: {0}".format(str(args.type)))
        sys.exit(1)
      sys.exit(0)

  except Exception as e:
    log.error("(in-toto-keygen) {0}: {1}".format(type(e).__name__, e))
    sys.exit(1)

if __name__ == "__main__":
  main()
