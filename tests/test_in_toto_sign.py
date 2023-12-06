# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  test_in_toto_sign.py
<Author>
  Sachit Malik <i.sachitmalik@gmail.com>
  Lukas Puehringer <luk.puehringer@gmail.com>
<Started>
  Wed Jun 21, 2017
<Copyright>
  See LICENSE for licensing information.
<Purpose>
  Test in_toto_sign command line tool.
"""

import json
import shutil
import unittest
from pathlib import Path
from unittest import mock

from in_toto.in_toto_sign import main as in_toto_sign_main
from tests.common import CliTestCase, GPGKeysMixin, TmpDirMixin


class TestInTotoSignTool(CliTestCase, TmpDirMixin, GPGKeysMixin):
    """Test in_toto_sign's main() - requires sys.argv patching; error logs/exits
    on Exception."""

    cli_main_func = staticmethod(in_toto_sign_main)

    @classmethod
    def setUpClass(cls):
        cls.set_up_test_dir()
        cls.set_up_gpg_keys()

        demo_files = Path(__file__).parent / "demo_files"
        pems = Path(__file__).parent / "pems"

        layout_name = "demo.layout.template"
        link_name = "package.2f89b927.link"
        for name in [layout_name, link_name]:
            shutil.copy(demo_files / name, name)

        cls.layout_path = layout_name
        cls.link_path = link_name

        cls.key_pw = "hunter2"

        cls.alice_path = str(pems / "rsa_private_unencrypted.pem")
        cls.alice_enc_path = str(pems / "rsa_private_encrypted.pem")
        cls.alice_pub_path = str(pems / "rsa_public.pem")

        cls.bob_path = str(pems / "ecdsa_private_unencrypted.pem")
        cls.bob_enc_path = str(pems / "ecdsa_private_encrypted.pem")
        cls.bob_pub_path = str(pems / "ecdsa_public.pem")

        cls.carl_path = str(pems / "ed25519_private_unencrypted.pem")
        cls.carl_enc_path = str(pems / "ed25519_private_encrypted.pem")
        cls.carl_pub_path = str(pems / "ed25519_public.pem")

    @classmethod
    def tearDownClass(cls):
        cls.tear_down_test_dir()

    def test_sign_and_verify(self):
        """Test signing and verifying Layout and Link metadata with
        different combinations of arguments."""

        # Sign Layout with multiple keys and write to "tmp.layout"
        self.assert_cli_sys_exit(
            [
                "-f",
                self.layout_path,
                "-k",
                self.alice_path,
                self.bob_path,
                "-o",
                "tmp.layout",
            ],
            0,
        )

        # Verify "tmp.layout" (requires all keys)
        self.assert_cli_sys_exit(
            [
                "-f",
                "tmp.layout",
                "-k",
                self.alice_pub_path,
                self.bob_pub_path,
                "--verify",
            ],
            0,
        )

        # Sign Layout "tmp.layout", appending new signature, write to "tmp.layout"
        self.assert_cli_sys_exit(
            ["-f", "tmp.layout", "-k", self.carl_path, "-a"], 0
        )

        # Verify "tmp.layout" (has three signatures now)
        self.assert_cli_sys_exit(
            [
                "-f",
                "tmp.layout",
                "-k",
                self.alice_pub_path,
                self.bob_pub_path,
                self.carl_pub_path,
                "--verify",
            ],
            0,
        )

        # Sign Link, replacing old signature
        # and write to same file as input
        self.assert_cli_sys_exit(
            [
                "-f",
                self.link_path,
                "-k",
                self.bob_path,
                "-o",
                self.link_path,
            ],
            0,
        )

        # Verify Link
        self.assert_cli_sys_exit(
            ["-f", self.link_path, "-k", self.bob_pub_path, "--verify"], 0
        )

        # Replace signature to Link and store to new file using passed
        # key's (alice) id as infix
        self.assert_cli_sys_exit(
            ["-f", self.link_path, "-k", self.alice_path], 0
        )
        # Verify Link with alice's keyid as infix
        self.assert_cli_sys_exit(
            [
                "-f",
                "package.2f685fa7.link",
                "-k",
                self.alice_pub_path,
                "--verify",
            ],
            0,
        )

        # Sign Layout with default gpg key
        self.assert_cli_sys_exit(
            [
                "-f",
                self.layout_path,
                "-g",
                "-o",
                "tmp_gpg.layout",
                "--gpg-home",
                self.gnupg_home,
            ],
            0,
        )
        # Verify Layout signed with default gpg key
        self.assert_cli_sys_exit(
            [
                "-f",
                "tmp_gpg.layout",
                "-g",
                self.gpg_key_0c8a17,
                "--gpg-home",
                self.gnupg_home,
                "--verify",
            ],
            0,
        )

        # Sign Layout with two gpg keys
        self.assert_cli_sys_exit(
            [
                "-f",
                self.layout_path,
                "-g",
                self.gpg_key_768c43,
                self.gpg_key_85da58,
                "-o",
                "tmp_gpg.layout",
                "--gpg-home",
                self.gnupg_home,
            ],
            0,
        )
        self.assert_cli_sys_exit(
            [
                "-f",
                "tmp_gpg.layout",
                "-g",
                self.gpg_key_768c43,
                self.gpg_key_85da58,
                "--gpg-home",
                self.gnupg_home,
                "--verify",
            ],
            0,
        )

        # Sign Layout with encrypted rsa/ed25519/ecdsa keys, prompting for pw, and verify
        with mock.patch(
            "in_toto.in_toto_sign.getpass", return_value=self.key_pw
        ):
            self.assert_cli_sys_exit(
                [
                    "-f",
                    self.layout_path,
                    "-k",
                    self.alice_enc_path,
                    self.bob_enc_path,
                    self.carl_enc_path,
                    "--prompt",
                    "-o",
                    "signed_with_encrypted_keys.layout",
                ],
                0,
            )
        self.assert_cli_sys_exit(
            [
                "-f",
                "signed_with_encrypted_keys.layout",
                "-k",
                self.alice_pub_path,
                self.bob_pub_path,
                self.alice_pub_path,
                "--verify",
            ],
            0,
        )

    def test_fail_signing(self):
        # Fail signing with invalid key
        self.assert_cli_sys_exit(
            [
                "-f",
                self.layout_path,
                "-k",
                self.carl_path,
                self.link_path,
            ],
            2,
        )

        # Fail with encrypted rsa key but no password
        self.assert_cli_sys_exit(
            ["-f", self.layout_path, "-k", self.alice_enc_path], 2
        )

        # Fail with encrypted ed25519 key but no password
        self.assert_cli_sys_exit(
            [
                "-f",
                self.layout_path,
                "-k",
                self.bob_enc_path,
            ],
            2,
        )

    def test_fail_verification(self):
        """Fail signature verification."""
        # Fail with wrong key (not used for signing)
        self.assert_cli_sys_exit(
            ["-f", self.layout_path, "-k", self.carl_pub_path, "--verify"], 1
        )

        # Fail with wrong key (not a valid pub key)
        self.assert_cli_sys_exit(
            ["-f", self.layout_path, "-k", self.carl_path, "--verify"], 2
        )

        # Fail with wrong gpg keyid (not used for signing)
        self.assert_cli_sys_exit(
            [
                "-f",
                self.layout_path,
                "-g",
                self.gpg_key_0c8a17,
                "--gpg-home",
                self.gnupg_home,
                "--verify",
            ],
            1,
        )

        # Fail with wrong gpg keyid (not a valid keyid)
        self.assert_cli_sys_exit(
            [
                "-f",
                self.layout_path,
                "-g",
                "bogus-gpg-keyid",
                "--gpg-home",
                self.gnupg_home,
                "--verify",
            ],
            2,
        )

    def test_bad_args(self):
        """Fail with wrong combination of arguments."""

        # Conflicting "verify" and signing options (--verify -o)
        self.assert_cli_sys_exit(
            [
                "-f",
                self.layout_path,
                "-k",
                "key-not-used",
                "--verify",
                "-o",
                "file-not-written",
            ],
            2,
        )

        # Conflicting "verify" and signing options (--verify -oa)
        self.assert_cli_sys_exit(
            [
                "-f",
                self.layout_path,
                "-k",
                "key-not-used",
                "--verify",
                "-a",
            ],
            2,
        )

        # Wrong "append" option for Link metadata
        self.assert_cli_sys_exit(
            ["-f", self.link_path, "-k", "key-not-used", "-a"], 2
        )

        # Wrong multiple keys for Link metadata
        self.assert_cli_sys_exit(
            [
                "-f",
                self.link_path,
                "-k",
                self.alice_path,
                self.bob_path,
            ],
            2,
        )

        # Wrong multiple gpg keys for Link metadata
        self.assert_cli_sys_exit(
            [
                "-f",
                self.link_path,
                "-g",
                self.gpg_key_768c43,
                self.gpg_key_85da58,
            ],
            2,
        )

        # Only one of gpg or regular key can be passed
        self.assert_cli_sys_exit(
            ["-f", self.layout_path, "-k", self.alice_path, "-g"], 2
        )

        # At least one of gpg or regular key must be passed
        self.assert_cli_sys_exit(
            [
                "-f",
                self.layout_path,
            ],
            2,
        )

        # For verification if gpg option is passed there must be a key id argument
        self.assert_cli_sys_exit(["-f", self.layout_path, "--verify", "-g"], 2)

    def test_bad_metadata(self):
        """Fail with wrong metadata."""

        # Not valid JSON
        self.assert_cli_sys_exit(
            [
                "-f",
                self.alice_pub_path,
                "-k",
                "key-not-used",
            ],
            2,
        )

        # Valid JSON but not valid Link or Layout
        with open("tmp.json", "wb") as f:
            f.write(json.dumps({}).encode("utf-8"))

        self.assert_cli_sys_exit(
            [
                "-f",
                "tmp.json",
                "-k",
                "key-not-used",
            ],
            2,
        )


class TestInTotoSignToolWithDSSE(CliTestCase, TmpDirMixin, GPGKeysMixin):
    """Test in_toto_sign's main() for dsse metadata files - requires sys.argv
    patching; error logs/exits on Exception."""

    cli_main_func = staticmethod(in_toto_sign_main)

    @classmethod
    def setUpClass(cls):
        cls.set_up_test_dir()
        cls.set_up_gpg_keys()

        pems = Path(__file__).parent / "pems"
        demo_dsse_files = Path(__file__).parent / "demo_dsse_files"
        layout_name = "demo.layout.template"
        link_name = "package.2f89b927.link"
        for name in [layout_name, link_name]:
            shutil.copy(demo_dsse_files / name, name)

        cls.layout_path = layout_name
        cls.link_path = link_name

        cls.key_pw = "hunter2"

        cls.alice_path = str(pems / "rsa_private_unencrypted.pem")
        cls.alice_enc_path = str(pems / "rsa_private_encrypted.pem")
        cls.alice_pub_path = str(pems / "rsa_public.pem")

        cls.bob_path = str(pems / "ecdsa_private_unencrypted.pem")
        cls.bob_enc_path = str(pems / "ecdsa_private_encrypted.pem")
        cls.bob_pub_path = str(pems / "ecdsa_public.pem")

        cls.carl_path = str(pems / "ed25519_private_unencrypted.pem")
        cls.carl_enc_path = str(pems / "ed25519_private_encrypted.pem")
        cls.carl_pub_path = str(pems / "ed25519_public.pem")

    @classmethod
    def tearDownClass(cls):
        cls.tear_down_test_dir()

    def test_sign_and_verify(self):
        """Test signing and verifying Layout and Link metadata with
        different combinations of arguments."""

        # Sign Layout with multiple keys and write to "tmp.layout"
        self.assert_cli_sys_exit(
            [
                "-f",
                self.layout_path,
                "-k",
                self.alice_path,
                self.bob_path,
                "-o",
                "tmp.layout",
            ],
            0,
        )

        # Verify "tmp.layout" (requires all keys)
        self.assert_cli_sys_exit(
            [
                "-f",
                "tmp.layout",
                "-k",
                self.alice_pub_path,
                self.bob_pub_path,
                "--verify",
            ],
            0,
        )

        # Sign Layout "tmp.layout", appending new signature, write to "tmp.layout"
        self.assert_cli_sys_exit(
            ["-f", "tmp.layout", "-k", self.carl_path, "-a"], 0
        )

        # Verify "tmp.layout" (has three signatures now)
        self.assert_cli_sys_exit(
            [
                "-f",
                "tmp.layout",
                "-k",
                self.alice_pub_path,
                self.bob_pub_path,
                self.carl_pub_path,
                "--verify",
            ],
            0,
        )

        # Sign Link, replacing old signature
        # and write to same file as input
        self.assert_cli_sys_exit(
            [
                "-f",
                self.link_path,
                "-k",
                self.bob_path,
                "-o",
                self.link_path,
            ],
            0,
        )

        # Verify Link
        self.assert_cli_sys_exit(
            ["-f", self.link_path, "-k", self.bob_pub_path, "--verify"], 0
        )

        # Replace signature to Link and store to new file using passed
        # key's (alice) id as infix
        self.assert_cli_sys_exit(
            ["-f", self.link_path, "-k", self.alice_path], 0
        )
        # Verify Link with alice's keyid as infix
        self.assert_cli_sys_exit(
            [
                "-f",
                "package.2f685fa7.link",
                "-k",
                self.alice_pub_path,
                "--verify",
            ],
            0,
        )

    def test_fail_verification(self):
        """Fail signature verification."""
        # Fail with wrong key (not used for signing)
        self.assert_cli_sys_exit(
            ["-f", self.layout_path, "-k", self.carl_pub_path, "--verify"], 1
        )

        # Fail with wrong gpg keyid (not used for signing)
        self.assert_cli_sys_exit(
            [
                "-f",
                self.layout_path,
                "-g",
                self.gpg_key_0c8a17,
                "--gpg-home",
                self.gnupg_home,
                "--verify",
            ],
            2,
        )


if __name__ == "__main__":
    unittest.main()
