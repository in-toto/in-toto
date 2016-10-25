import os
import sys
import pickle
import json
import getpass

import toto.ssl_crypto.keys
import toto.ssl_crypto.formats
import toto.log as log


def generate_and_write_rsa_keypair(filepath, password):
  """
  <Purpose>
    Generate an RSA key file, create an encrypted PEM string (using 'password'
    as the pass phrase), and store it in 'filepath'.  The public key portion of
    the generated RSA key is stored in <'filepath'>.pub

  <Arguments>
    filepath:
      The public and private key files are saved to <filepath>.pub, <filepath>
      respectively

    password:
      The password used to encrypt 'filepath'

  <Exceptions>
    ssl_commons.FormatError, if the arguments are improperly formatted

  <Side Effects>
    Writes key files to '<filepath>' and '<filepath>.pub'

  <Returns>
    None.
  """

  toto.ssl_crypto.formats.PATH_SCHEMA.check_match(filepath)
  toto.ssl_crypto.formats.PASSWORD_SCHEMA.check_match(password)

  rsa_key = toto.ssl_crypto.keys.generate_rsa_key()

  public = rsa_key['keyval']['public']
  private = rsa_key['keyval']['private']
  private_pem = toto.ssl_crypto.keys.create_rsa_encrypted_pem(private, password)

  with open(filepath + '.pub', 'w') as fo_public:
    fo_public.write(public.encode('utf-8'))

  with open(filepath, 'w') as fo_private:
    fo_private.write(private_pem.encode('utf-8'))


def import_rsa_key_from_file(filepath, password=None):
  """
  <Purpose>
    Import the RSA key stored in PEM format to 'filepath'. This could be
    a public key or a private key.
    If a password is specified, the key will be decrypted

  <Arguments>
    filepath:
      <filepath> file, an RSA PEM file

    password (optional):
      if a password is specified, the imported key will be decrypted

  <Exceptions>
    ssl_commons.FormatError, if the arguments are improperly formatted

  <Side Effects>
    'filepath' is read and its contents extracted

  <Returns>
    An RSA key object conformant to 'tuf.formats.RSAKEY_SCHEMA'
  """

  toto.ssl_crypto.formats.PATH_SCHEMA.check_match(filepath)

  with open(filepath, 'rb') as fo_pem:
    rsa_pem = fo_pem.read().decode('utf-8')

  if password:
    toto.ssl_crypto.formats.PASSWORD_SCHEMA.check_match(password)
    rsa_key = toto.ssl_crypto.keys.import_rsakey_from_encrypted_pem(rsa_pem,
        password)
  else:
    rsa_key = toto.ssl_crypto.keys.format_rsakey_from_pem(rsa_pem)

  return rsa_key


def prompt_password(prompt="Enter password: "):
  """Prompts for password input and returns the password"""
  return getpass.getpass(prompt, sys.stderr)


def prompt_import_rsa_key_from_file(filepath):
  """Prompts for password and calls import_rsa_key_from_file"""
  password = prompt_password()
  return import_rsa_key_from_file(filepath, password)


def prompt_generate_and_write_rsa_keypair(filepath):
  """Prompts for password and generates and calls
  generate_and_write_rsa_keypair"""
  password = prompt_password()
  generate_and_write_rsa_keypair(filepath, password)

