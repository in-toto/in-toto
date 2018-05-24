import sys
import getpass

import in_toto.gpg.functions
import in_toto.gpg.formats
import securesystemslib.formats
import securesystemslib.hash
import securesystemslib.interface
import securesystemslib.keys
import securesystemslib.exceptions

from in_toto.exceptions import UnsupportedKeyTypeError
from securesystemslib.interface import (import_ed25519_privatekey_from_file,
    import_ed25519_publickey_from_file)

DEFAULT_RSA_KEY_BITS = 3072

KEY_TYPE_RSA = 'rsa'
KEY_TYPE_ED25519 = 'ed25519'

SUPPORTED_KEY_TYPES = [KEY_TYPE_ED25519, KEY_TYPE_RSA]


def generate_and_write_rsa_keypair(filepath, bits=DEFAULT_RSA_KEY_BITS,
    password=""):
  """
  <Purpose>
    Calls securesystemslib.interface.generate_and_write_rsa_keypair with
    a default password of "" so as to prevent the library from prompting for
    password. If prompting is needed, it's already handled here and then
    forwarded.

  <Arguments>
    filepath:
      <filepath> is where to write the private key. Public key is written to
      <filepath>.pub

    bits (optional):
      Key size of the rsa key generated.

    password: (optional)
      Password to be used to encrypt the private key created.

  <Exceptions>
    Only those from securesystemslib.interface.generate_and_write_rsa_keypair

  <Side Effects>
    Same as securesystemslib.interface.generate_and_write_rsa_keypair

  <Returns>
    None.
  """
  securesystemslib.interface.generate_and_write_rsa_keypair(filepath, bits,
      password)


def generate_and_write_ed25519_keypair(filepath, password=""):
  """
  <Purpose>
    Calls securesystemslib.interface.generate_and_write_ed25519_keypair with
    a default password of "" so as to prevent the library from prompting for
    password. If prompting is needed, it's already handled here and then
    forwarded.

  <Arguments>
    filepath:
      <filepath> is where to write the private key. Public key is written to
      <filepath>.pub

    password: (optional)
      Password to be used to encrypt the private key created.

  <Exceptions>
    Same as securesystemslib.interface.generate_and_write_ed25519_keypair

  <Side Effects>
    Same as securesystemslib.interface.generate_and_write_ed25519_keypair

  <Returns>
    None.
  """
  securesystemslib.interface.generate_and_write_ed25519_keypair(filepath,
      password)


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
        rsa_pem, password=password)

  elif securesystemslib.keys.is_pem_public(rsa_pem):
    rsa_key = securesystemslib.keys.import_rsakey_from_public_pem(rsa_pem)
  else:
    raise securesystemslib.exceptions.FormatError(
        "The key has to be clear either a private or"
        " public RSA key in PEM format")

  return rsa_key


def import_public_keys_from_files_as_dict(filepaths, key_types=None):
  """
  <Purpose>
    Takes a list of filepaths to RSA public keys and returns them as a
    dictionary conformant with securesystemslib.formats.KEYDICT_SCHEMA.

  <Arguments>
    filepaths:
      List of paths to the public keys.

    key_types: (optional)
      List types of each of the keys being imported into the dict. If not
      specified, all keys are assumed to be RSA.

  <Exceptions>
    securesystemslib.exceptions.FormatError, if the arguments are
    don't have the same length.

    UnsupportedKeyTypeError, if the key_type specified is unsupported.

  <Side Effects>
    Each file in 'filepaths' is read and its contents extracted

  <Returns>
    A key dict object conformant with securesystemslib.formats.KEYDICT_SCHEMA
  """
  # are key_types needed?
  # we could figure it out using the key format

  if key_types is None:
    key_types = [KEY_TYPE_RSA] * len(filepaths)

  if len(key_types) != len(filepaths):
    raise securesystemslib.exceptions.FormatError(
        "number of key_types should match with the number"
        " of layout keys specified")

  key_dict = {}
  for idx, filepath in enumerate(filepaths):

    if key_types[idx] == KEY_TYPE_ED25519:
      key = import_ed25519_publickey_from_file(filepath)
    elif key_types[idx] == KEY_TYPE_RSA:
      key = import_rsa_key_from_file(filepath)
    else:  # pragma: no cover
      # This branch is never possible as argparse already checks valid keys
      # via the choices parameter.
      raise UnsupportedKeyTypeError('Unsupported keytype: ' + key_types[idx])

    securesystemslib.formats.PUBLIC_KEY_SCHEMA.check_match(key)
    keyid = key["keyid"]
    key_dict[keyid] = key
  return key_dict


def import_gpg_public_keys_from_keyring_as_dict(keyids, gpg_home=False):
  """Creates a dictionary of gpg public keys retrieving gpg public keys
  identified by the list of passed `keyids` from the gpg keyring at `gpg_home`.
  If `gpg_home` is False the default keyring is used. """
  key_dict = {}
  for gpg_keyid in keyids:
    pub_key = in_toto.gpg.functions.gpg_export_pubkey(gpg_keyid,
        homedir=gpg_home)
    in_toto.gpg.formats.PUBKEY_SCHEMA.check_match(pub_key)
    keyid = pub_key["keyid"]
    key_dict[keyid] = pub_key
  return key_dict


def prompt_password(prompt="Enter password: "):
  """Prompts for password input and returns the password. """
  return getpass.getpass(prompt, sys.stderr)


def import_private_key_from_file(filepath, key_type):
  """
  <Purpose>
    Tries to load a key with/without password. If a CryptoError
    occurs, prompts the user for a password and tries to load the key again.

  <Arguments>
    filepath:
      <filepath> file, a private key file

    key_type: (optional)
      Type of the private key being imported. If not
      specified, the key is assumed to be RSA.

  <Exceptions>
    UnsupportedKeyTypeError, if the key_type specified is unsupported.

  <Side Effects>
    'filepath' is read and its contents extracted

  <Returns>
    A private key object conformant with securesystemslib.formats.KEY_SCHEMA
  """
  if key_type == KEY_TYPE_ED25519:
    key = prompt_import_ed25519_privatekey_from_file(filepath)
  elif key_type == KEY_TYPE_RSA:
    key = prompt_import_rsa_key_from_file(filepath)
  else:  # pragma: no cover
    # This branch is never possible as argparse already checks valid keys
    # via the choices parameter.
    raise UnsupportedKeyTypeError('Unsupported keytype: ' + key_type)

  return key


def prompt_import_ed25519_privatekey_from_file(filepath):
  """Tries to load an Ed25519 private key without password. If a CryptoError
  occurs, prompts the user for a password and tries to load the key again.
  """
  password = None
  try:
    import_ed25519_privatekey_from_file(filepath, password)
  except securesystemslib.exceptions.CryptoError:
    password = prompt_password()
  return import_ed25519_privatekey_from_file(filepath, password)


def prompt_import_rsa_key_from_file(filepath):
  """Tries to load an RSA key without password. If a CryptoError occurs, prompts
  the user for a password and tries to load the key again. """
  password = None
  try:
    import_rsa_key_from_file(filepath, password)
  except securesystemslib.exceptions.CryptoError:
    password = prompt_password()
  return import_rsa_key_from_file(filepath, password)


def prompt_generate_and_write_rsa_keypair(filepath, bits):
  """Prompts for password and calls
  generate_and_write_rsa_keypair"""
  password = prompt_password()
  generate_and_write_rsa_keypair(filepath, bits, password)


def prompt_generate_and_write_ed25519_keypair(filepath):
  """Prompts for password and calls
  generate_and_write_ed25519_keypair"""
  password = prompt_password()
  generate_and_write_ed25519_keypair(filepath, password)
