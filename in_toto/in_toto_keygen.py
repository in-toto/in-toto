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
  <filename>.pub for private and public keys respectively.

  General Usage:
  python in_toto_keygen.py [-p] <filename>

  Example Usage:
  Suppose Bob wants to create the keys and dump them with file name
  "bob_keys". He also wants to encrypt the so created private key with his
  choice of passphrase. The keys would then be created, the private key
  would be encrypted and dumped as "bob_keys" and public key would be dumped
  as "bob_keys.pub".

  python in_toto_keygen.py -p bob_keys

"""
import os
import sys
import argparse
import json
import getpass
import in_toto.util
import securesystemslib.formats
import securesystemslib.keys
import securesystemslib.exceptions


def generate_and_write_rsa_keypair(filepath, password=None):
  """
  <Purpose>
    Generate an RSA key keypair and store public and private portion each
    to a file in PEM format.
    If a password is specified the private key is encrypted using that password
    as pass phrase.
    The private key is stored to <'filepath'> and the public key to
    <'filepath'>.pub

  <Arguments>
    filepath:
      The public and private key files are saved to <filepath>.pub, <filepath>
      respectively
    password: (optional)
      If specified the password is used to encrypt the private key

  <Exceptions>
    securesystemslib.exceptions.FormatError, if the arguments are
    improperly formatted

  <Side Effects>
    Writes key files to '<filepath>' and '<filepath>.pub'

  <Returns>
    None.
  """
  securesystemslib.formats.PATH_SCHEMA.check_match(filepath)

  rsa_key = securesystemslib.keys.generate_rsa_key()

  public = rsa_key["keyval"]["public"]
  private = rsa_key["keyval"]["private"]

  if password:
    private_pem = securesystemslib.keys.create_rsa_encrypted_pem(
        private, password)
  else:
    private_pem = private

  with open(filepath + ".pub", "w") as fo_public:
    fo_public.write(public.encode("utf-8"))

  with open(filepath, "w") as fo_private:
    fo_private.write(private_pem.encode("utf-8"))

def prompt_password(prompt="Enter password: "):
  """Prompts for password input and returns the password. """
  return getpass.getpass(prompt, sys.stderr)

def prompt_generate_and_write_rsa_keypair(filepath):
  """Prompts for password and calls
  generate_and_write_rsa_keypair"""
  password = prompt_password()
  generate_and_write_rsa_keypair(filepath, password)


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

  in_toto_args.add_argument("name", type=string,
                            help="The filename of the resulting key files",
                            metavar="<filename>")

  args = parser.parse_args()
  args.operator = args.operator.lower()

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
      prompt_generate_and_write_rsa_keypair(args.name)
      sys.exit(0)
    else:
      generate_and_write_rsa_keypair(args.name, password=None)
      sys.exit(0)

  except Exception as e:
    print('The following error occurred', e)
    sys.exit(1)

if __name__ == "__main__":
    main()
