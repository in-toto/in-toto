#!/usr/bin/env python

# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  test_gpg.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Jan 28, 2023

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test _LegacyGPGKey, _LegacyGPGSigner and _LegacyGPGSignature class methods.
"""

import unittest

from securesystemslib.gpg.functions import export_pubkey
from securesystemslib.gpg.constants import have_gpg

from in_toto.models.gpg import (_LegacyGPGKey, _LegacyGPGSignature,
  _LegacyGPGSigner)

from tests.common import GPGKeysMixin, TmpDirMixin


@unittest.skipIf(not have_gpg(), "gpg not found")
class TestLegacyGPGKeyAndSigner(unittest.TestCase, TmpDirMixin, GPGKeysMixin):
  """Test RSA gpg signature creation and verification."""

  @classmethod
  def setUpClass(cls):
    cls.set_up_test_dir()
    cls.set_up_gpg_keys()

    cls.test_data = b"test_data"
    cls.wrong_data = b"something malicious"

    cls.default_keyid = cls.gpg_key_0C8A17
    cls.signing_subkey_keyid = cls.gpg_key_D924E9

    cls.default_key_dict = export_pubkey(cls.default_keyid, cls.gnupg_home)

  @classmethod
  def tearDownClass(self):
    self.tear_down_test_dir()

  def test_gpg_sign_and_verify_object_with_default_key(self):
    """Create and verify a signature using the default key on the keyring."""

    # Create a signature.
    signer = _LegacyGPGSigner(homedir=self.gnupg_home)
    signature = signer.sign(self.test_data)

    # Generate Key from gnupg keyring.
    key = _LegacyGPGKey.from_keyring(self.default_keyid, self.gnupg_home)

    self.assertTrue(key.verify_signature(signature, self.test_data))
    self.assertFalse(key.verify_signature(signature, self.wrong_data))

    # Generate Key from dict.
    key = _LegacyGPGKey.from_legacy_dict(self.default_key_dict)

    self.assertTrue(key.verify_signature(signature, self.test_data))
    self.assertFalse(key.verify_signature(signature, self.wrong_data))

  def test_gpg_sign_and_verify_object(self):
    """Create and verify a signature using the specific key on the keyring."""

    # Create a signature.
    signer = _LegacyGPGSigner(self.signing_subkey_keyid, self.gnupg_home)
    signature = signer.sign(self.test_data)

    # Generate Key from gnupg keyring.
    key = _LegacyGPGKey.from_keyring(self.signing_subkey_keyid, self.gnupg_home)

    self.assertTrue(key.verify_signature(signature, self.test_data))
    self.assertFalse(key.verify_signature(signature, self.wrong_data))

    # Generate Key from dict.
    key_dict = export_pubkey(self.signing_subkey_keyid, self.gnupg_home)
    key = _LegacyGPGKey.from_dict(key_dict["keyid"], key_dict)

    self.assertTrue(key.verify_signature(signature, self.test_data))
    self.assertFalse(key.verify_signature(signature, self.wrong_data))

  def test_gpg_signer_serialization(self):
    """Tests from_dict and to_dict methods of GPGSignature."""

    sig_dict = {
      "keyid": "f4f90403af58eef6",
      "signature": "c39f86e70e12e70e11d87eb7e3ab7d3b",
      "other_headers": "d8f8a89b5d71f07b842a",
    }

    signature = _LegacyGPGSignature.from_dict(sig_dict)
    self.assertEqual(sig_dict, signature.to_dict())

  def test_gpg_key_serialization(self):
    """Test to check serialization methods of GPGKey."""

    # Test loading and dumping of GPGKey.
    key = _LegacyGPGKey.from_legacy_dict(self.default_key_dict)
    self.assertEqual(key.to_dict(), self.default_key_dict)

    # Test loading and dumping of GPGKey from keyring.
    key = _LegacyGPGKey.from_keyring(self.default_keyid, self.gnupg_home)
    self.assertEqual(key.to_dict(), self.default_key_dict)

  def test_gpg_key_equality(self):
    """Test to check equality between two GPGKey."""

    # Generate two GPGkey.
    key1 = _LegacyGPGKey.from_legacy_dict(self.default_key_dict)
    key2 = _LegacyGPGKey.from_legacy_dict(self.default_key_dict)

    self.assertNotEqual(self.default_key_dict, key1)
    self.assertEqual(key2, key1)

    # Assert equality of key created from dict of first GPGKey.
    key2 = _LegacyGPGKey.from_legacy_dict(key1.to_dict())
    self.assertEqual(key2, key1)

    # Assert Inequalities.
    key2.type = "invalid"
    self.assertNotEqual(key2, key1)
    key2.type = key1.type

    key2.subkeys = {}
    self.assertNotEqual(key2, key1)
    key2.subkeys = key1.subkeys

    key2.keyval = {}
    self.assertNotEqual(key2, key1)
    key2.keyval = key1.keyval

    self.assertEqual(key2, key1)
