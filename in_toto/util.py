import sys
import getpass

import in_toto.gpg.functions
import in_toto.gpg.formats
import securesystemslib.formats
import securesystemslib.hash
import securesystemslib.keys
import securesystemslib.exceptions

DEFAULT_RSA_KEY_BITS = 3072

def generate_and_write_rsa_keypair(filepath, bits=DEFAULT_RSA_KEY_BITS,
    password=None):
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

  rsa_key = securesystemslib.keys.generate_rsa_key(bits)

  public = rsa_key["keyval"]["public"]
  private = rsa_key["keyval"]["private"]

  if password:
    private_pem = securesystemslib.keys.create_rsa_encrypted_pem(
        private, password)
  else:
    private_pem = private

  with open(filepath + ".pub", "wb") as fo_public:
    fo_public.write(public.encode("utf-8"))

  with open(filepath, "wb") as fo_private:
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
        rsa_pem, password=password)

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


def prompt_import_rsa_key_from_file(filepath):
  """Trys to load the key without password. If a CryptoError occurs, prompts
  the user for a password and trys to load the the key again. """
  password = None
  try:
    import_rsa_key_from_file(filepath)
  except securesystemslib.exceptions.CryptoError:
    password = prompt_password()
  return import_rsa_key_from_file(filepath, password)


def prompt_generate_and_write_rsa_keypair(filepath, bits):
  """Prompts for password and calls
  generate_and_write_rsa_keypair"""
  password = prompt_password()
  generate_and_write_rsa_keypair(filepath, bits, password)
