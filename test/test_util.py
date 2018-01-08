#!/usr/bin/env python

"""
<Program Name>
  test_verifylib.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Jan 17, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test util functions.

"""

import os
import shutil
import tempfile
import unittest
from mock import patch

import in_toto.formats
from in_toto.util import (generate_and_write_rsa_keypair,
    import_rsa_key_from_file, import_rsa_public_keys_from_files_as_dict,
    prompt_password, prompt_generate_and_write_rsa_keypair,
    prompt_import_rsa_key_from_file,
    import_gpg_public_keys_from_keyring_as_dict)

import securesystemslib.formats
import securesystemslib.exceptions

class TestUtil(unittest.TestCase):
  """Test various util functions. Mostly related to RSA key creation or
  loading."""

  @classmethod
  def setUpClass(self):
    # Create directory where the verification will take place
    self.working_dir = os.getcwd()
    self.test_dir = os.path.realpath(tempfile.mkdtemp())

    # Copy gpg keyring
    gpg_keyring_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "gpg_keyrings", "rsa")
    self.gnupg_home = os.path.join(self.test_dir, "rsa")
    shutil.copytree(gpg_keyring_path, self.gnupg_home)

    os.chdir(self.test_dir)

  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp test directory. """
    os.chdir(self.working_dir)
    shutil.rmtree(self.test_dir)

  def test_create_and_import_rsa(self):
    """Create RS key and import private and public key separately. """
    name = "key1"
    generate_and_write_rsa_keypair(name)
    private_key = import_rsa_key_from_file(name)
    public_key = import_rsa_key_from_file(name + ".pub")

    securesystemslib.formats.KEY_SCHEMA.check_match(private_key)
    self.assertTrue(private_key["keyval"].get("private"))
    self.assertTrue(
        securesystemslib.formats.PUBLIC_KEY_SCHEMA.matches(public_key))

  def test_create_and_import_encrypted_rsa(self):
    """Create ecrypted RSA key and import private and public key separately. """
    name = "key2"
    password = "123456"
    bits = 3072
    generate_and_write_rsa_keypair(name, bits, password)
    private_key = import_rsa_key_from_file(name, password)
    public_key = import_rsa_key_from_file(name + ".pub")

    securesystemslib.formats.KEY_SCHEMA.check_match(private_key)
    self.assertTrue(private_key["keyval"].get("private"))
    self.assertTrue(
        securesystemslib.formats.PUBLIC_KEY_SCHEMA.matches(public_key))

  def test_create_and_import_encrypted_rsa_no_password(self):
    """Try import encrypted RSA key without or wrong pw, raises exception. """
    name = "key3"
    password = "123456"
    bits = 3072
    generate_and_write_rsa_keypair(name, bits, password)
    with self.assertRaises(securesystemslib.exceptions.CryptoError):
      private_key = import_rsa_key_from_file(name)
    with self.assertRaises(securesystemslib.exceptions.CryptoError):
      private_key = import_rsa_key_from_file(name, "wrong-password")

  def test_import_non_existing_rsa(self):
    """Try import non-existing RSA key, raises exception. """
    with self.assertRaises(IOError):
      import_rsa_key_from_file("key-does-not-exist")

  def test_import_rsa_wrong_format(self):
    """Try import wrongly formatted RSA key, raises exception. """
    not_an_rsa = "not_an_rsa"
    open(not_an_rsa, "w").write(not_an_rsa)
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      import_rsa_key_from_file(not_an_rsa)

  def test_import_rsa_public_keys_from_files_as_dict(self):
    """Create and import multiple rsa public keys and return KEYDICT. """
    name1 = "key4"
    name2 = "key5"
    generate_and_write_rsa_keypair(name1)
    generate_and_write_rsa_keypair(name2)

    # Succefully import public keys as keydictionary
    key_dict = import_rsa_public_keys_from_files_as_dict([name1 + ".pub",
        name2 + ".pub"])
    securesystemslib.formats.KEYDICT_SCHEMA.check_match(key_dict)

    # Import wrongly formatted key raises an exception
    not_an_rsa = "not_an_rsa"
    open(not_an_rsa, "w").write(not_an_rsa)
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      import_rsa_public_keys_from_files_as_dict([name1 + ".pub", not_an_rsa])

    # Import private key raises an exception
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      import_rsa_public_keys_from_files_as_dict([name1, name2])

  def test_import_gpg_public_keys_from_keyring_as_dict(self):
    """Import gpg public keys from keyring and return KEYDICT. """

    keyids = [
      "8465a1e2e0fb2b40adb2478e18fb3f537e0c8a17",
      "7b3abb26b97b655ab9296bd15b0bd02e1c768c43",
      "8288ef560ed3795f9df2c0db56193089b285da58"
    ]

    # Succefully import public keys from keychain as keydictionary
    key_dict = import_gpg_public_keys_from_keyring_as_dict(keyids,
        gpg_home=self.gnupg_home)
    in_toto.formats.ANY_PUBKEY_DICT_SCHEMA.check_match(key_dict)
    self.assertListEqual(sorted(keyids), sorted(key_dict.keys()))

    # Try to import key with invalid keyid
    with self.assertRaises(ValueError):
      key_dict = import_gpg_public_keys_from_keyring_as_dict(["bogus-key"],
          gpg_home=self.gnupg_home)

    # Try to import key that does not exist
    with self.assertRaises(ValueError):
      key_dict = import_gpg_public_keys_from_keyring_as_dict(["aaaa"],
            gpg_home=self.gnupg_home)

  def test_prompt_password(self):
    """Call password prompt. """
    password = "123456"
    with patch("getpass.getpass", return_value=password):
      self.assertEqual(prompt_password(), password)

  def test_prompt_create_and_import_encrypted_rsa(self):
    """Create and import password encrypted RSA using prompt input. """
    key = "key6"
    password = "123456"
    bits = 3072
    with patch("getpass.getpass", return_value=password):
      prompt_generate_and_write_rsa_keypair(key,bits)
      rsa_key = prompt_import_rsa_key_from_file(key)
      securesystemslib.formats.KEY_SCHEMA.check_match(rsa_key)
      self.assertTrue(rsa_key["keyval"].get("private"))

    with patch("getpass.getpass",
        return_value="wrong-password"), self.assertRaises(
        securesystemslib.exceptions.CryptoError):
      prompt_import_rsa_key_from_file(key)


if __name__ == "__main__":
  unittest.main()
