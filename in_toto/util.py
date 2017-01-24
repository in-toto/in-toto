import os
import sys
import pickle
import json
import getpass

from in_toto import log
import securesystemslib.formats
import securesystemslib.hash
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


def import_rsa_key_from_file(filepath, password=None):
  """
  <Purpose>
    Import the RSA key stored in PEM format to 'filepath'. This can be
    a public key or a private key.
    If it is a private key and the password is specified, it will be used
    to decrypt the private key.

  <Arguments>
    filepath:
      <filepath> file, an RSA PEM file

    password: (optional)
      If a password is specified, the imported private key will be decrypted

  <Exceptions>
    securesystemslib.exceptions.FormatError, if the arguments are
    improperly formatted

  <Side Effects>
    'filepath' is read and its contents extracted

  <Returns>
    An RSA key object conformant to 'tuf.formats.RSAKEY_SCHEMA'
  """
  securesystemslib.formats.PATH_SCHEMA.check_match(filepath)

  with open(filepath, "rb") as fo_pem:
    rsa_pem = fo_pem.read().decode("utf-8")

  if securesystemslib.keys.is_pem_private(rsa_pem):
    rsa_key = securesystemslib.keys.import_rsakey_from_private_pem(
        rsa_pem, password)

  elif securesystemslib.keys.is_pem_public(rsa_pem):
    rsa_key = securesystemslib.keys.import_rsakey_from_public_pem(rsa_pem)
  else:
    raise securesystemslib.exceptions.FormatError(
        "The key has to be clear either a private or"
        " public RSA key in PEM format")

  return rsa_key

def import_rsa_public_keys_from_files_as_dict(filepaths):
  """Takes a list of filepaths to RSA public keys and returns them as a
  dictionary conformant with securesystemslib.formats.KEYDICT_SCHEMA."""
  key_dict = {}
  for filepath in filepaths:
    key = import_rsa_key_from_file(filepath)
    securesystemslib.formats.PUBLIC_KEY_SCHEMA.check_match(key)
    keyid = key["keyid"]
    key_dict[keyid] = key
  return key_dict

def prompt_password(prompt="Enter password: "):
  """Prompts for password input and returns the password. """
  return getpass.getpass(prompt, sys.stderr)


def prompt_import_rsa_key_from_file(filepath):
  """Trys to load the key without password. If a CryptoError occurs, prompts
  the user for a password and trys to load the the key again. """
  password = None
  try:
    import_rsa_key_from_file(filepath)
  except securesystemslib.exceptions.CryptoError, e:
    password = prompt_password()
  return import_rsa_key_from_file(filepath, password)


def prompt_generate_and_write_rsa_keypair(filepath):
  """Prompts for password and generates and calls
  generate_and_write_rsa_keypair"""
  password = prompt_password()
  generate_and_write_rsa_keypair(filepath, password)


def flatten_and_invert_artifact_dict(artifact_dict, hash_algorithm="sha256"):
  """
  <Purpose>
    Flattens an and inverts artifact_dict in the format of:
    { <path> : HASHDICT_SCHEMA }.

    >>> artifacts = {
    >>> "foo": {
    >>>   "sha512" : "23432df87ab",
    >>>   "sha256" : "34324abc34df",
    >>>   }
    >>> }
    >>> flat_artifacts = flatten_and_invert_artifact_dict(artifacts)
    >>> flat_artifacts == {"34324abc34df" : "foo"}
    True

  <Arguments>
    artifact_dict:
      The artifact_dict to flatten and invert.

    hash_algorithm: (optional)
      Use the hash generated with the specified hash_algorithm.

  <Exceptions>
    securesystemslib.exceptions.FormatError, if the arguments are
    improperly formatted

  <Side Effects>
    None.

  <Returns>
    A dictionary with artifact hashes as keys and artifact paths as values.
  """
  securesystemslib.formats.HASHALGORITHMS_SCHEMA.check_match(
      [hash_algorithm])

  inverted_dict = {}
  for file_path, hash_dict in artifact_dict.iteritems():
    securesystemslib.formats.HASHDICT_SCHEMA.check_match(hash_dict)
    file_hash = hash_dict[hash_algorithm]
    inverted_dict[file_hash] = file_path

  return inverted_dict
