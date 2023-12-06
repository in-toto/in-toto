#!/usr/bin/env python

# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  test_in_toto_verify.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Jan 9, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test in_toto_verify command line tool.

"""

import os
import shutil
import unittest
from pathlib import Path

from securesystemslib.gpg.constants import have_gpg
from securesystemslib.interface import (
    import_ed25519_privatekey_from_file,
    import_rsa_privatekey_from_file,
)
from securesystemslib.signer import SSlibSigner

from in_toto.in_toto_verify import main as in_toto_verify_main
from in_toto.models._signer import load_crypto_signer_from_pkcs8_file
from in_toto.models.metadata import Metadata
from tests.common import CliTestCase, GPGKeysMixin, TmpDirMixin

DEMO_FILES = Path(__file__).parent / "demo_files"
DEMO_FILES_DSSE = Path(__file__).parent / "demo_dsse_files"
PEMS = Path(__file__).parent / "pems"
SCRIPTS = Path(__file__).parent / "scripts"


class TestInTotoVerifyTool(CliTestCase, TmpDirMixin):
    """
    Tests
      - in_toto_verify's main() - requires sys.argv patching;
      - in_toto_verify - calls verifylib.in_toto_verify and error logs/exits
        in case of a raised Exception.

    Uses in-toto demo supply chain link metadata files and basic layout for
    verification:

    Copies the basic layout for different test scenarios:
      - signed layout
      - multiple signed layout (using two project owner keys)
    """

    cli_main_func = staticmethod(in_toto_verify_main)

    @classmethod
    def setUpClass(cls):
        """Creates and changes into temporary directory.
        Copies demo files to temp dir...
          - owner/functionary key pairs
          - *.link metadata files
          - layout template (not signed, no expiration date)
          - final product

        ...and dumps various layouts for different test scenarios
        """

        # Find demo files
        demo_files = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_files"
        )
        # find where the scripts directory is located.
        scripts_directory = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "scripts"
        )

        cls.set_up_test_dir()

        # Copy demo files to temp dir
        for fn in os.listdir(demo_files):
            shutil.copy(os.path.join(demo_files, fn), cls.test_dir)

        shutil.copytree(scripts_directory, "scripts")

        # Load layout template
        layout_template = Metadata.load("demo.layout.template")

        # Store layout paths to be used in tests
        cls.layout_single_signed_path = "single-signed.layout"
        cls.layout_double_signed_path = "double-signed.layout"

        # Import layout signing keys
        alice = import_rsa_privatekey_from_file("alice")
        bob = import_rsa_privatekey_from_file("bob")
        cls.alice_path = "alice.pub"
        cls.bob_path = "bob.pub"

        # dump a single signed layout
        layout_template.sign(alice)
        layout_template.dump(cls.layout_single_signed_path)
        # dump a double signed layout
        layout_template.sign(bob)
        layout_template.dump(cls.layout_double_signed_path)

    @classmethod
    def tearDownClass(cls):
        cls.tear_down_test_dir()

    def test_main_required_args(self):
        """Test in-toto-verify CLI tool with required arguments."""
        args = [
            "--layout",
            self.layout_single_signed_path,
            "--layout-keys",
            self.alice_path,
        ]

        self.assert_cli_sys_exit(args, 0)

    def test_main_wrong_args(self):
        """Test in-toto-verify CLI tool with wrong arguments."""
        wrong_args_list = [
            [],
            ["--layout", self.layout_single_signed_path],
            ["--key", self.alice_path],
        ]

        for wrong_args in wrong_args_list:
            self.assert_cli_sys_exit(wrong_args, 2)

    def test_main_multiple_keys(self):
        """Test in-toto-verify CLI tool with multiple keys."""
        args = [
            "--layout",
            self.layout_double_signed_path,
            "--layout-keys",
            self.alice_path,
            self.bob_path,
        ]
        self.assert_cli_sys_exit(args, 0)

    def test_main_failing_bad_layout_path(self):
        """Test in-toto-verify CLI tool with bad layout path."""
        args = ["-l", "not-a-path-to-a-layout", "-k", self.alice_path]
        self.assert_cli_sys_exit(args, 1)

    def test_main_link_dir(self):
        """Test in-toto-verify CLI tool with explicit link dir."""

        # Use current working directory explicitly to load links
        args = [
            "--layout",
            self.layout_single_signed_path,
            "--layout-keys",
            self.alice_path,
            "--link-dir",
            ".",
        ]
        self.assert_cli_sys_exit(args, 0)

        # Fail with an explicit link directory, where no links are found
        args = [
            "--layout",
            self.layout_single_signed_path,
            "--layout-keys",
            self.alice_path,
            "--link-dir",
            "bad-link-dir",
        ]
        self.assert_cli_sys_exit(args, 1)


class TestInTotoVerifyToolWithDSSE(CliTestCase, TmpDirMixin):
    """
    Tests
      - in_toto_verify's main() - requires sys.argv patching;
      - in_toto_verify - calls verifylib.in_toto_verify and error logs/exits
        in case of a raised Exception.

    Uses in-toto demo supply chain link metadata files and basic layout for
    verification:

    Copies the basic layout for different test scenarios:
      - signed layout
      - multiple signed layout (using two project owner keys)
    """

    cli_main_func = staticmethod(in_toto_verify_main)

    @classmethod
    def setUpClass(cls):
        """Creates and changes into temporary directory.
        Copies demo files to temp dir...
          - owner/functionary key pairs
          - *.link metadata files
          - layout template (not signed, no expiration date)
          - final product

        ...and dumps various layouts for different test scenarios
        """

        # Find demo files
        demo_files = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_files"
        )

        # Demo DSSE Metadata Files
        demo_dsse_files = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_dsse_files"
        )

        # find where the scripts directory is located.
        scripts_directory = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "scripts"
        )

        cls.set_up_test_dir()

        # Copy demo files to temp dir
        for fn in os.listdir(demo_files):
            shutil.copy(os.path.join(demo_files, fn), cls.test_dir)

        for fn in os.listdir(demo_dsse_files):
            shutil.copy(os.path.join(demo_dsse_files, fn), cls.test_dir)

        shutil.copytree(scripts_directory, "scripts")

        # Load layout template
        layout_template = Metadata.load("demo.layout.template")

        # Store layout paths to be used in tests
        cls.layout_single_signed_path = "single-signed.layout"
        cls.layout_double_signed_path = "double-signed.layout"

        # Import layout signing keys
        alice = import_rsa_privatekey_from_file("alice")
        bob = import_rsa_privatekey_from_file("bob")
        cls.alice_path = "alice.pub"
        cls.bob_path = "bob.pub"

        # dump a single signed layout
        layout_template.create_signature(SSlibSigner(alice))
        layout_template.dump(cls.layout_single_signed_path)
        # dump a double signed layout
        layout_template.create_signature(SSlibSigner(bob))
        layout_template.dump(cls.layout_double_signed_path)

    @classmethod
    def tearDownClass(cls):
        cls.tear_down_test_dir()

    def test_main_required_args(self):
        """Test in-toto-verify CLI tool with required arguments."""
        args = [
            "--layout",
            self.layout_single_signed_path,
            "--layout-keys",
            self.alice_path,
        ]

        self.assert_cli_sys_exit(args, 0)

    def test_main_multiple_keys(self):
        """Test in-toto-verify CLI tool with multiple keys."""
        args = [
            "--layout",
            self.layout_double_signed_path,
            "--layout-keys",
            self.alice_path,
            self.bob_path,
        ]
        self.assert_cli_sys_exit(args, 0)

    def test_main_link_dir(self):
        """Test in-toto-verify CLI tool with explicit link dir."""

        # Use current working directory explicitly to load links
        args = [
            "--layout",
            self.layout_single_signed_path,
            "--layout-keys",
            self.alice_path,
            "--link-dir",
            ".",
        ]
        self.assert_cli_sys_exit(args, 0)

        # Fail with an explicit link directory, where no links are found
        args = [
            "--layout",
            self.layout_single_signed_path,
            "--layout-keys",
            self.alice_path,
            "--link-dir",
            "bad-link-dir",
        ]
        self.assert_cli_sys_exit(args, 1)


class TestInTotoVerifyToolMixedKeys(CliTestCase, TmpDirMixin):
    """Tests in-toto-verify like TestInTotoVerifyTool but with
    both rsa and ed25519 project owner and functionary keys."""

    cli_main_func = staticmethod(in_toto_verify_main)

    @classmethod
    def setUpClass(cls):
        """Creates and changes into temporary directory.
        Copies demo files to temp dir...
          - owner/functionary key pairs
          - *.link metadata files
          - layout template (not signed, no expiration date)
          - final product

        ...and dumps layout for test scenario
        """
        # Find demo files
        demo_files = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_files"
        )

        scripts_directory = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "scripts"
        )

        cls.set_up_test_dir()

        # Copy demo files to temp dir
        for fn in os.listdir(demo_files):
            shutil.copy(os.path.join(demo_files, fn), cls.test_dir)

        shutil.copytree(scripts_directory, "scripts")

        # Load layout template
        layout_template = Metadata.load("demo.layout.template")

        # Store layout paths to be used in tests
        cls.layout_double_signed_path = "double-signed.layout"

        # Import layout signing keys
        alice = import_rsa_privatekey_from_file("alice")
        danny = import_ed25519_privatekey_from_file("danny")
        cls.alice_path = "alice.pub"
        cls.danny_path = "danny.pub"

        # dump a double signed layout
        layout_template.sign(alice)
        layout_template.sign(danny)
        layout_template.dump(cls.layout_double_signed_path)

    @classmethod
    def tearDownClass(cls):
        cls.tear_down_test_dir()

    def test_main_multiple_keys(self):
        """Test in-toto-verify CLI tool with multiple keys."""
        args = [
            "--layout",
            self.layout_double_signed_path,
            "--layout-keys",
            self.alice_path,
            self.danny_path,
            "--key-types",
            "rsa",
            "ed25519",
        ]
        self.assert_cli_sys_exit(args, 0)


class TestInTotoVerifyToolMixedKeysWithDSSE(CliTestCase, TmpDirMixin):
    """Tests in-toto-verify like TestInTotoVerifyTool but with
    both rsa and ed25519 project owner and functionary keys."""

    cli_main_func = staticmethod(in_toto_verify_main)

    @classmethod
    def setUpClass(cls):
        """Creates and changes into temporary directory.
        Copies demo files to temp dir...
          - owner/functionary key pairs
          - *.link metadata files
          - layout template (not signed, no expiration date)
          - final product

        ...and dumps layout for test scenario
        """
        # Find demo files
        demo_files = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_files"
        )

        # Demo DSSE Metadata Files
        demo_dsse_files = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_dsse_files"
        )

        # find where the scripts directory is located.
        scripts_directory = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "scripts"
        )

        cls.set_up_test_dir()

        # Copy demo files to temp dir
        for fn in os.listdir(demo_files):
            shutil.copy(os.path.join(demo_files, fn), cls.test_dir)

        for fn in os.listdir(demo_dsse_files):
            shutil.copy(os.path.join(demo_dsse_files, fn), cls.test_dir)

        shutil.copytree(scripts_directory, "scripts")

        # Load layout template
        layout_template = Metadata.load("demo.layout.template")

        # Store layout paths to be used in tests
        cls.layout_double_signed_path = "double-signed.layout"

        # Import layout signing keys
        alice = import_rsa_privatekey_from_file("alice")
        danny = import_ed25519_privatekey_from_file("danny")
        cls.alice_path = "alice.pub"
        cls.danny_path = "danny.pub"

        # dump a double signed layout
        layout_template.create_signature(SSlibSigner(alice))
        layout_template.create_signature(SSlibSigner(danny))
        layout_template.dump(cls.layout_double_signed_path)

    @classmethod
    def tearDownClass(cls):
        cls.tear_down_test_dir()

    def test_main_multiple_keys(self):
        """Test in-toto-verify CLI tool with multiple keys."""
        args = [
            "--layout",
            self.layout_double_signed_path,
            "--layout-keys",
            self.alice_path,
            self.danny_path,
            "--key-types",
            "rsa",
            "ed25519",
        ]
        self.assert_cli_sys_exit(args, 0)


@unittest.skipIf(not have_gpg(), "gpg not found")
class TestInTotoVerifyToolGPG(CliTestCase, TmpDirMixin, GPGKeysMixin):
    """Tests in-toto-verify like TestInTotoVerifyTool but with
    gpg project owner and functionary keys."""

    cli_main_func = staticmethod(in_toto_verify_main)

    @classmethod
    def setUpClass(cls):
        """Copy test gpg rsa keyring, gpg demo metadata files and demo final
        product to tmp test dir."""
        # Copy gpg demo metadata files
        demo_files = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_files_gpg"
        )

        # find where the scripts directory is located.
        scripts_directory = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "scripts"
        )

        cls.set_up_test_dir()
        cls.set_up_gpg_keys()

        for fn in os.listdir(demo_files):
            shutil.copy(os.path.join(demo_files, fn), cls.test_dir)

        # Change into test dir
        shutil.copytree(scripts_directory, "scripts")

        # Sign layout template with gpg key
        layout_template = Metadata.load("demo.layout.template")

        cls.layout_path = "gpg_signed.layout"
        layout_template.sign_gpg(cls.gpg_key_0c8a17, cls.gnupg_home)
        layout_template.dump(cls.layout_path)

    @classmethod
    def tearDownClass(cls):
        cls.tear_down_test_dir()

    def test_gpg_signed_layout_with_gpg_functionary_keys(self):
        """Successfully test demo supply chain where the layout lists gpg keys
        as functionary keys and is signed with a gpg key."""
        args = [
            "--layout",
            self.layout_path,
            "--gpg",
            self.gpg_key_0c8a17,
            "--gpg-home",
            self.gnupg_home,
        ]

        self.assert_cli_sys_exit(args, 0)


class TestInTotoVerifySubjectPublicKeyInfoKeys(CliTestCase, TmpDirMixin):
    """Tests in-toto-verify like TestInTotoVerifyTool but with
    standard PEM/SubjectPublicKeyInfo keys."""

    cli_main_func = staticmethod(in_toto_verify_main)

    @classmethod
    def setUpClass(cls):
        """Creates and changes into temporary directory.

        * Copy files needed for verification:
            - demo *.link files
            - final product
            - inspection scripts

        * Sign layout with keys in "pems" dir
        * Dump layout

        """
        cls.set_up_test_dir()

        # Copy demo files and inspection scripts
        for demo_file in [
            "foo.tar.gz",
            "package.2f89b927.link",
            "write-code.776a00e2.link",
        ]:
            shutil.copy(DEMO_FILES / demo_file, demo_file)

        shutil.copytree(SCRIPTS, "scripts")

        # Load layout template
        layout_template = Metadata.load(
            str(DEMO_FILES / "demo.layout.template")
        )

        # Load keys and sign
        cls.public_key_paths = []
        for keytype in ["rsa", "ed25519", "ecdsa"]:
            cls.public_key_paths.append(str(PEMS / f"{keytype}_public.pem"))
            signer = load_crypto_signer_from_pkcs8_file(
                PEMS / f"{keytype}_private_unencrypted.pem"
            )

            layout_template.create_signature(signer)

        layout_template.dump("demo.layout")

    @classmethod
    def tearDownClass(cls):
        cls.tear_down_test_dir()

    def test_main_multiple_keys(self):
        """Test in-toto-verify CLI tool with multiple keys."""

        args = [
            "--layout",
            "demo.layout",
            "--verification-keys",
        ] + self.public_key_paths
        self.assert_cli_sys_exit(args, 0)


class TestInTotoVerifySubjectPublicKeyInfoKeysAndUseDSSE(
    CliTestCase, TmpDirMixin
):
    """Tests in-toto-verify like TestInTotoVerifyTool but with
    standard PEM/SubjectPublicKeyInfo keys."""

    cli_main_func = staticmethod(in_toto_verify_main)

    @classmethod
    def setUpClass(cls):
        """Creates and changes into temporary directory.

        * Copy files needed for verification:
            - demo *.link files (dsse)
            - final product
            - inspection scripts

        * Sign layout with keys in "pems" dir
        * Dump layout

        """
        cls.set_up_test_dir()

        # Copy demo files and inspection scripts
        for dsse_link in [
            "package.2f89b927.link",
            "write-code.776a00e2.link",
        ]:
            shutil.copy(DEMO_FILES_DSSE / dsse_link, dsse_link)
        shutil.copy(DEMO_FILES / "foo.tar.gz", "foo.tar.gz")
        shutil.copytree(SCRIPTS, "scripts")

        # Load layout template
        layout_template = Metadata.load(
            str(DEMO_FILES_DSSE / "demo.layout.template")
        )

        # Load keys and sign
        cls.public_key_paths = []
        for keytype in ["rsa", "ed25519", "ecdsa"]:
            cls.public_key_paths.append(str(PEMS / f"{keytype}_public.pem"))
            signer = load_crypto_signer_from_pkcs8_file(
                PEMS / f"{keytype}_private_unencrypted.pem"
            )

            layout_template.create_signature(signer)

        layout_template.dump("demo.layout")

    @classmethod
    def tearDownClass(cls):
        cls.tear_down_test_dir()

    def test_main_multiple_keys(self):
        """Test in-toto-verify CLI tool with multiple keys."""

        args = [
            "--layout",
            "demo.layout",
            "--verification-keys",
        ] + self.public_key_paths
        self.assert_cli_sys_exit(args, 0)


if __name__ == "__main__":
    unittest.main()
