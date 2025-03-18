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

from securesystemslib._gpg.constants import have_gpg

from in_toto.in_toto_verify import main as in_toto_verify_main
from in_toto.models._signer import load_crypto_signer_from_pkcs8_file
from in_toto.models.metadata import Metadata
from tests.common import PEMS, CliTestCase, GPGKeysMixin, TmpDirMixin

DEMO_FILES = Path(__file__).parent / "demo_files"
DEMO_FILES_DSSE = Path(__file__).parent / "demo_dsse_files"
SCRIPTS = Path(__file__).parent / "scripts"


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

    def test_main_failing_bad_layout_path(self):
        """Test in-toto-verify CLI tool with bad layout path."""
        args = [
            "--layout",
            "not-a-path-to-a-layout",
            "--verification-keys",
        ] + self.public_key_paths
        self.assert_cli_sys_exit(args, 1)

    def test_main_link_dir(self):
        """Test in-toto-verify CLI tool with explicit link dir."""
        # Use current working directory explicitly to load links
        args = [
            "--layout",
            "demo.layout",
            "--link-dir",
            ".",
            "--verification-keys",
        ] + self.public_key_paths
        self.assert_cli_sys_exit(args, 0)

        # Fail with an explicit link directory, where no links are found
        args = [
            "--layout",
            "demo.layout",
            "--link-dir",
            "bad-link-dir",
            "--verification-keys",
        ] + self.public_key_paths
        self.assert_cli_sys_exit(args, 1)


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
