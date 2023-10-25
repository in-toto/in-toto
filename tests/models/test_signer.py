#!/usr/bin/env python

# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  test_signer.py

<Author>
  Pradyumna Krishna <git@onpy.in>

<Started>
  Jan 28, 2023

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test GPGKey, GPGSigner and GPGSignature class methods.
"""

import unittest
from pathlib import Path

from securesystemslib.exceptions import (
    UnverifiedSignatureError,
    VerificationError,
)
from securesystemslib.gpg.constants import have_gpg
from securesystemslib.gpg.functions import export_pubkey

from in_toto.models._signer import (
    GPGKey,
    GPGSignature,
    GPGSigner,
    load_crypto_signer_from_pkcs8_file,
)
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

        cls.default_keyid = cls.gpg_key_0c8a17
        cls.signing_subkey_keyid = cls.gpg_key_d92439
        cls.expired_keyid = "e8ac80c924116dabb51d4b987cb07d6d2c199c7c"

        cls.default_key_dict = export_pubkey(cls.default_keyid, cls.gnupg_home)

    @classmethod
    def tearDownClass(cls):
        cls.tear_down_test_dir()

    def test_gpg_sign_and_verify_object_with_default_key(self):
        """Create and verify a signature using the default key on the keyring."""

        # Create a signature.
        signer = GPGSigner(homedir=self.gnupg_home)
        signature = signer.sign(self.test_data)

        # Generate Key from gnupg keyring.
        key = GPGKey.from_keyring(self.default_keyid, self.gnupg_home)

        key.verify_signature(signature, self.test_data)
        with self.assertRaises(UnverifiedSignatureError):
            key.verify_signature(signature, self.wrong_data)

        # Generate Key from dict.
        key = GPGKey.from_legacy_dict(self.default_key_dict)

        key.verify_signature(signature, self.test_data)
        with self.assertRaises(UnverifiedSignatureError):
            key.verify_signature(signature, self.wrong_data)

    def test_gpg_sign_and_verify_object(self):
        """Create and verify a signature using the specific key on the keyring."""

        # Create a signature.
        signer = GPGSigner(self.signing_subkey_keyid, self.gnupg_home)
        signature = signer.sign(self.test_data)

        # Generate Key from gnupg keyring.
        key = GPGKey.from_keyring(self.signing_subkey_keyid, self.gnupg_home)

        key.verify_signature(signature, self.test_data)
        with self.assertRaises(UnverifiedSignatureError):
            key.verify_signature(signature, self.wrong_data)

        # Generate Key from dict.
        key_dict = export_pubkey(self.signing_subkey_keyid, self.gnupg_home)
        key = GPGKey.from_dict(key_dict["keyid"], key_dict)

        key.verify_signature(signature, self.test_data)
        with self.assertRaises(UnverifiedSignatureError):
            key.verify_signature(signature, self.wrong_data)

    def test_verify_using_expired_keyid(self):
        """Creates and verifies a signature using expired key on the keyring."""

        # Create a signature.
        signer = GPGSigner(self.signing_subkey_keyid, self.gnupg_home)
        signature = signer.sign(self.test_data)

        # Verify signature using expired key.
        key = GPGKey.from_keyring(self.expired_keyid, self.gnupg_home)
        with self.assertRaises(VerificationError):
            key.verify_signature(signature, self.test_data)

    def test_gpg_signature_serialization(self):
        """Tests from_dict and to_dict methods of GPGSignature."""

        sig_dict = {
            "keyid": "f4f90403af58eef6",
            "signature": "c39f86e70e12e70e11d87eb7e3ab7d3b",
            "other_headers": "d8f8a89b5d71f07b842a",
        }

        signature = GPGSignature.from_dict(sig_dict)
        self.assertEqual(sig_dict, signature.to_dict())

    def test_gpg_key_serialization(self):
        """Test to check serialization methods of GPGKey."""

        # Test loading and dumping of GPGKey.
        key = GPGKey.from_legacy_dict(self.default_key_dict)
        self.assertEqual(key.to_dict(), self.default_key_dict)

        # Test loading and dumping of GPGKey from keyring.
        key = GPGKey.from_keyring(self.default_keyid, self.gnupg_home)
        self.assertEqual(key.to_dict(), self.default_key_dict)

    def test_gpg_key_equality(self):
        """Test to check equality between two GPGKey."""

        # Generate two GPGkey.
        key1 = GPGKey.from_legacy_dict(self.default_key_dict)
        key2 = GPGKey.from_legacy_dict(self.default_key_dict)

        self.assertNotEqual(self.default_key_dict, key1)
        self.assertEqual(key2, key1)

        # Assert equality of key created from dict of first GPGKey.
        key2 = GPGKey.from_legacy_dict(key1.to_dict())
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


class TestCryptoSigner(unittest.TestCase):
    """Test helper to load CryptoSigner"""

    def test_load_keys(self):
        pems_dir = Path(__file__).parent.parent / "pems"

        for algo in ["rsa", "ecdsa", "ed25519"]:
            path = pems_dir / f"{algo}_private_unencrypted.pem"
            signer = load_crypto_signer_from_pkcs8_file(path)
            self.assertEqual(signer.public_key.keytype, algo)

            path = pems_dir / f"{algo}_private_encrypted.pem"
            signer2 = load_crypto_signer_from_pkcs8_file(path, b"hunter2")
            self.assertEqual(
                signer.public_key.to_dict(), signer2.public_key.to_dict()
            )


if __name__ == "__main__":
    unittest.main()
