#!/usr/bin/env python

# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  test_in_toto_record.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Nov 28, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test in_toto_record command line tool.

"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from in_toto.in_toto_record import main as in_toto_record_main
from in_toto.models.link import UNFINISHED_FILENAME_FORMAT
from tests.common import CliTestCase, GenKeysMixin, GPGKeysMixin, TmpDirMixin


class TestInTotoRecordTool(
    CliTestCase, TmpDirMixin, GPGKeysMixin, GenKeysMixin
):
    """Test in_toto_record's main() - requires sys.argv patching; and
    in_toto_record_start/in_toto_record_stop - calls runlib and error logs/exits
    on Exception."""

    cli_main_func = staticmethod(in_toto_record_main)

    @classmethod
    def setUpClass(cls):
        """Create and change into temporary directory,
        generate key pair, dummy artifact and base arguments."""
        cls.set_up_test_dir()
        cls.set_up_gpg_keys()
        cls.set_up_keys()

        cls.test_artifact1 = "test_artifact1"
        cls.test_artifact2 = "test_artifact2"
        Path(cls.test_artifact1).touch()
        Path(cls.test_artifact2).touch()

    @classmethod
    def tearDownClass(cls):
        cls.tear_down_test_dir()

    def test_start_stop(self):
        """Test CLI command record start/stop with various arguments."""
        # pylint: disable=too-many-statements

        # Start/stop recording using rsa key
        args = ["--step-name", "test1", "--key", self.rsa_key_path]
        self.assert_cli_sys_exit(["start"] + args, 0)
        self.assert_cli_sys_exit(["stop"] + args, 0)

        # Start/stop recording using encrypted rsa key with password on prompt
        args = [
            "--step-name",
            "test1.1",
            "--key",
            self.rsa_key_enc_path,
            "--password",
        ]
        with mock.patch(
            "securesystemslib.interface.get_password", return_value=self.key_pw
        ):
            self.assert_cli_sys_exit(["start"] + args, 0)
            self.assert_cli_sys_exit(["stop"] + args, 0)

        # Start/stop recording using encrypted rsa key passing the pw
        args = [
            "--step-name",
            "test1.2",
            "--key",
            self.rsa_key_enc_path,
            "--password",
            self.key_pw,
        ]
        self.assert_cli_sys_exit(["start"] + args, 0)
        self.assert_cli_sys_exit(["stop"] + args, 0)

        # Start/stop with recording one artifact using rsa key
        args = ["--step-name", "test2", "--key", self.rsa_key_path]
        self.assert_cli_sys_exit(
            ["start"] + args + ["--materials", self.test_artifact1], 0
        )
        self.assert_cli_sys_exit(
            ["stop"] + args + ["--products", self.test_artifact1], 0
        )

        # Start/stop with excluding one artifact using rsa key
        args = ["--step-name", "test2.5", "--key", self.rsa_key_path]
        self.assert_cli_sys_exit(
            ["start"]
            + args
            + ["--materials", self.test_artifact1, "--exclude", "test*"],
            0,
        )
        self.assert_cli_sys_exit(
            ["stop"]
            + args
            + ["--products", self.test_artifact1, "--exclude", "test*"],
            0,
        )

        # Start/stop with base-path using rsa key
        args = [
            "--step-name",
            "test2.6",
            "--key",
            self.rsa_key_path,
            "--base-path",
            self.test_dir,
        ]
        self.assert_cli_sys_exit(["start"] + args, 0)
        self.assert_cli_sys_exit(["stop"] + args, 0)

        # Start/stop with recording multiple artifacts using rsa key
        args = ["--step-name", "test3", "--key", self.rsa_key_path]
        self.assert_cli_sys_exit(
            ["start"]
            + args
            + ["--materials", self.test_artifact1, self.test_artifact2],
            0,
        )
        self.assert_cli_sys_exit(
            ["stop"]
            + args
            + ["--products", self.test_artifact2, self.test_artifact2],
            0,
        )

        # Start/stop recording using ed25519 key
        args = [
            "--step-name",
            "test4",
            "--key",
            self.ed25519_key_path,
            "--key-type",
            "ed25519",
        ]
        self.assert_cli_sys_exit(["start"] + args, 0)
        self.assert_cli_sys_exit(["stop"] + args, 0)

        # Start/stop with encrypted ed25519 key entering password on the prompt
        args = [
            "--step-name",
            "test4.1",
            "--key",
            self.ed25519_key_enc_path,
            "--key-type",
            "ed25519",
            "--password",
        ]
        with mock.patch(
            "securesystemslib.interface.get_password", return_value=self.key_pw
        ):
            self.assert_cli_sys_exit(["start"] + args, 0)
            self.assert_cli_sys_exit(["stop"] + args, 0)

        # Start/stop with encrypted ed25519 key passing the password
        args = [
            "--step-name",
            "test4.2",
            "--key",
            self.ed25519_key_enc_path,
            "--key-type",
            "ed25519",
            "--password",
            self.key_pw,
        ]
        self.assert_cli_sys_exit(["start"] + args, 0)
        self.assert_cli_sys_exit(["stop"] + args, 0)

        # Start/stop with recording one artifact using ed25519 key
        args = [
            "--step-name",
            "test5",
            "--key",
            self.ed25519_key_path,
            "--key-type",
            "ed25519",
        ]
        self.assert_cli_sys_exit(
            ["start"] + args + ["--materials", self.test_artifact1], 0
        )
        self.assert_cli_sys_exit(
            ["stop"] + args + ["--products", self.test_artifact1], 0
        )

        # Start/stop with excluding one artifact using ed25519 key
        args = [
            "--step-name",
            "test5.5",
            "--key",
            self.ed25519_key_path,
            "--key-type",
            "ed25519",
        ]
        self.assert_cli_sys_exit(
            ["start"]
            + args
            + ["--materials", self.test_artifact1, "--exclude", "test*"],
            0,
        )
        self.assert_cli_sys_exit(
            ["stop"]
            + args
            + ["--products", self.test_artifact1, "--exclude", "test*"],
            0,
        )

        # Start/stop with base-path using ed25519 key
        args = [
            "--step-name",
            "test5.6",
            "--key",
            self.ed25519_key_path,
            "--key-type",
            "ed25519",
            "--base-path",
            self.test_dir,
        ]
        self.assert_cli_sys_exit(["start"] + args, 0)
        self.assert_cli_sys_exit(["stop"] + args, 0)

        # Start/stop with recording multiple artifacts using ed25519 key
        args = [
            "--step-name",
            "test6",
            "--key",
            self.ed25519_key_path,
            "--key-type",
            "ed25519",
        ]
        self.assert_cli_sys_exit(
            ["start"]
            + args
            + ["--materials", self.test_artifact1, self.test_artifact2],
            0,
        )
        self.assert_cli_sys_exit(
            ["stop"]
            + args
            + ["--products", self.test_artifact2, self.test_artifact2],
            0,
        )

        # Start/stop sign with specified gpg keyid
        args = [
            "--step-name",
            "test7",
            "--gpg",
            self.gpg_key_768c43,
            "--gpg-home",
            self.gnupg_home,
        ]
        self.assert_cli_sys_exit(["start"] + args, 0)
        self.assert_cli_sys_exit(["stop"] + args, 0)

        # Start/stop sign with default gpg keyid
        args = ["--step-name", "test8", "--gpg", "--gpg-home", self.gnupg_home]
        self.assert_cli_sys_exit(["start"] + args, 0)
        self.assert_cli_sys_exit(["stop"] + args, 0)

        # Start/stop sign with metadata directory
        args = ["--step-name", "test9", "--key", self.rsa_key_path]
        tmp_dir = os.path.realpath(tempfile.mkdtemp(dir=os.getcwd()))
        metadata_directory_arg = ["--metadata-directory", tmp_dir]
        self.assert_cli_sys_exit(["start"] + args, 0)
        self.assert_cli_sys_exit(["stop"] + metadata_directory_arg + args, 0)

    def test_glob_no_unfinished_files(self):
        """Test record stop with missing unfinished files when globbing (gpg)."""
        args = [
            "--step-name",
            "test-no-glob",
            "--gpg",
            self.gpg_key_768c43,
            "--gpg-home",
            self.gnupg_home,
        ]
        self.assert_cli_sys_exit(["stop"] + args, 1)

    def test_glob_to_many_unfinished_files(self):
        """Test record stop with to many unfinished files when globbing (gpg)."""
        name = "test-to-many-glob"
        fn1 = UNFINISHED_FILENAME_FORMAT.format(
            step_name=name, keyid="a12345678"
        )
        fn2 = UNFINISHED_FILENAME_FORMAT.format(
            step_name=name, keyid="b12345678"
        )
        Path(fn1).touch()
        Path(fn2).touch()
        args = [
            "--step-name",
            name,
            "--gpg",
            self.gpg_key_768c43,
            "--gpg-home",
            self.gnupg_home,
        ]
        self.assert_cli_sys_exit(["stop"] + args, 1)

    def test_encrypted_key_but_no_pw(self):
        args = ["--step-name", "enc-key", "--key", self.rsa_key_enc_path]
        self.assert_cli_sys_exit(["start"] + args, 1)
        self.assert_cli_sys_exit(["stop"] + args, 1)

        args = [
            "--step-name",
            "enc-key",
            "--key",
            self.ed25519_key_enc_path,
            "--key-type",
            "ed25519",
        ]
        self.assert_cli_sys_exit(["start"] + args, 1)
        self.assert_cli_sys_exit(["stop"] + args, 1)

    def test_wrong_key(self):
        """Test CLI command record with wrong key exits 1"""
        args = ["--step-name", "wrong-key", "--key", "non-existing-key"]
        self.assert_cli_sys_exit(["start"] + args, 1)
        self.assert_cli_sys_exit(["stop"] + args, 1)

    def test_no_key(self):
        """Test if no key is specified, argparse error exists with 2"""
        args = ["--step-name", "no-key"]
        self.assert_cli_sys_exit(["start"] + args, 2)
        self.assert_cli_sys_exit(["stop"] + args, 2)

    def test_missing_unfinished_link(self):
        """Error exit with missing unfinished link file."""
        args = ["--step-name", "no-link", "--key", self.rsa_key_path]
        self.assert_cli_sys_exit(["stop"] + args, 1)

        args = [
            "--step-name",
            "no-link",
            "--key",
            self.ed25519_key_path,
            "--key-type",
            "ed25519",
        ]
        self.assert_cli_sys_exit(["stop"] + args, 1)

    def test_pkcs8_signing_key(self):
        """Test in-toto-record, sign link with pkcs8 key file for each algo."""
        pems_dir = Path(__file__).parent / "pems"
        args = ["-n", "foo", "--signing-key"]
        for algo, short_keyid in [
            ("rsa", "2f685fa7"),
            ("ecdsa", "50d7e110"),
            ("ed25519", "c6d8bf2e"),
        ]:
            link_path = Path(f"foo.{short_keyid}.link")
            unfinished_link_path = Path(f".foo.{short_keyid}.link-unfinished")

            # Use unencrypted key
            pem_path = pems_dir / f"{algo}_private_unencrypted.pem"
            self.assert_cli_sys_exit(["start"] + args + [str(pem_path)], 0)
            self.assertTrue(unfinished_link_path.exists())
            self.assert_cli_sys_exit(["stop"] + args + [str(pem_path)], 0)
            self.assertFalse(unfinished_link_path.exists())
            self.assertTrue(link_path.exists())
            link_path.unlink()

            # Fail with encrypted key, but no pw
            pem_path = pems_dir / f"{algo}_private_encrypted.pem"
            self.assert_cli_sys_exit(["start"] + args + [str(pem_path)], 1)
            self.assertFalse(unfinished_link_path.exists())

            # Use encrypted key, passing pw
            self.assert_cli_sys_exit(
                ["start"] + args + [str(pem_path), "-P", "hunter2"], 0
            )
            self.assertTrue(unfinished_link_path.exists())
            self.assert_cli_sys_exit(
                ["stop"] + args + [str(pem_path), "-P", "hunter2"], 0
            )
            self.assertFalse(unfinished_link_path.exists())
            self.assertTrue(link_path.exists())
            link_path.unlink()

            # Use encrypted key, mocking pw enter on prompt
            with mock.patch(
                "in_toto.in_toto_record.getpass", return_value="hunter2"
            ):
                self.assert_cli_sys_exit(
                    ["start"] + args + [str(pem_path), "-P"], 0
                )
                self.assertTrue(unfinished_link_path.exists())
                self.assert_cli_sys_exit(
                    ["stop"] + args + [str(pem_path), "-P"], 0
                )
                self.assertFalse(unfinished_link_path.exists())
                self.assertTrue(link_path.exists())
                link_path.unlink()


class TestInTotoRecordToolWithDSSE(
    CliTestCase, TmpDirMixin, GPGKeysMixin, GenKeysMixin
):
    """Test in_toto_record's main() with --use-dsse argument - requires sys.argv
    patching; and in_toto_record_start/in_toto_record_stop - calls runlib and
    error logs/exits on Exception."""

    cli_main_func = staticmethod(in_toto_record_main)

    @classmethod
    def setUpClass(cls):
        """Create and change into temporary directory,
        generate key pair, dummy artifact and base arguments."""
        cls.set_up_test_dir()
        cls.set_up_keys()

        cls.test_artifact1 = "test_artifact1"
        cls.test_artifact2 = "test_artifact2"
        Path(cls.test_artifact1).touch()
        Path(cls.test_artifact2).touch()

    @classmethod
    def tearDownClass(cls):
        cls.tear_down_test_dir()

    def test_start_stop(self):
        """Test CLI command record start/stop with various arguments."""

        # Start/stop recording using rsa key
        args = [
            "--step-name",
            "test1",
            "--key",
            self.rsa_key_path,
            "--use-dsse",
        ]
        self.assert_cli_sys_exit(["start"] + args, 0)
        self.assert_cli_sys_exit(["stop"] + args, 0)

        # Start/stop with recording one artifact using rsa key
        args = [
            "--step-name",
            "test2",
            "--key",
            self.rsa_key_path,
            "--use-dsse",
        ]
        self.assert_cli_sys_exit(
            ["start"] + args + ["--materials", self.test_artifact1], 0
        )
        self.assert_cli_sys_exit(
            ["stop"] + args + ["--products", self.test_artifact1], 0
        )

        # Start/stop with excluding one artifact using rsa key
        args = [
            "--step-name",
            "test2.5",
            "--key",
            self.rsa_key_path,
            "--use-dsse",
        ]
        self.assert_cli_sys_exit(
            ["start"]
            + args
            + ["--materials", self.test_artifact1, "--exclude", "test*"],
            0,
        )
        self.assert_cli_sys_exit(
            ["stop"]
            + args
            + ["--products", self.test_artifact1, "--exclude", "test*"],
            0,
        )

        # Start/stop with base-path using rsa key
        args = [
            "--step-name",
            "test2.6",
            "--key",
            self.rsa_key_path,
            "--base-path",
            self.test_dir,
            "--use-dsse",
        ]
        self.assert_cli_sys_exit(["start"] + args, 0)
        self.assert_cli_sys_exit(["stop"] + args, 0)

        # Start/stop with recording multiple artifacts using rsa key
        args = [
            "--step-name",
            "test3",
            "--key",
            self.rsa_key_path,
            "--use-dsse",
        ]
        self.assert_cli_sys_exit(
            ["start"]
            + args
            + ["--materials", self.test_artifact1, self.test_artifact2],
            0,
        )
        self.assert_cli_sys_exit(
            ["stop"]
            + args
            + ["--products", self.test_artifact2, self.test_artifact2],
            0,
        )

    def test_pkcs8_signing_key(self):
        """Test in-toto-record, sign link with pkcs8 key file for each algo."""
        pems_dir = Path(__file__).parent / "pems"
        args = ["-n", "foo", "--use-dsse", "--signing-key"]
        for algo, short_keyid in [
            ("rsa", "2f685fa7"),
            ("ecdsa", "50d7e110"),
            ("ed25519", "c6d8bf2e"),
        ]:
            link_path = Path(f"foo.{short_keyid}.link")
            unfinished_link_path = Path(f".foo.{short_keyid}.link-unfinished")

            # Use unencrypted key
            pem_path = pems_dir / f"{algo}_private_unencrypted.pem"
            self.assert_cli_sys_exit(["start"] + args + [str(pem_path)], 0)
            self.assertTrue(unfinished_link_path.exists())
            self.assert_cli_sys_exit(["stop"] + args + [str(pem_path)], 0)
            self.assertFalse(unfinished_link_path.exists())
            self.assertTrue(link_path.exists())
            link_path.unlink()

            # Fail with encrypted key, but no pw
            pem_path = pems_dir / f"{algo}_private_encrypted.pem"
            self.assert_cli_sys_exit(["start"] + args + [str(pem_path)], 1)
            self.assertFalse(unfinished_link_path.exists())

            # Use encrypted key, passing pw
            self.assert_cli_sys_exit(
                ["start"] + args + [str(pem_path), "-P", "hunter2"], 0
            )
            self.assertTrue(unfinished_link_path.exists())
            self.assert_cli_sys_exit(
                ["stop"] + args + [str(pem_path), "-P", "hunter2"], 0
            )
            self.assertFalse(unfinished_link_path.exists())
            self.assertTrue(link_path.exists())
            link_path.unlink()

            # Use encrypted key, mocking pw enter on prompt
            with mock.patch(
                "in_toto.in_toto_record.getpass", return_value="hunter2"
            ):
                self.assert_cli_sys_exit(
                    ["start"] + args + [str(pem_path), "-P"], 0
                )
                self.assertTrue(unfinished_link_path.exists())
                self.assert_cli_sys_exit(
                    ["stop"] + args + [str(pem_path), "-P"], 0
                )
                self.assertFalse(unfinished_link_path.exists())
                self.assertTrue(link_path.exists())
                link_path.unlink()


if __name__ == "__main__":
    unittest.main()
