#!/usr/bin/env python

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

import sys
import unittest
import tempfile
import os

if sys.version_info >= (3, 3):
  import unittest.mock as mock # pylint: disable=no-name-in-module,import-error
else:
  import mock # pylint: disable=import-error

from in_toto.models.link import UNFINISHED_FILENAME_FORMAT
from in_toto.in_toto_record import main as in_toto_record_main

from tests.common import CliTestCase, TmpDirMixin, GPGKeysMixin, GenKeysMixin

import securesystemslib.interface # pylint: disable=unused-import



class TestInTotoRecordTool(CliTestCase, TmpDirMixin, GPGKeysMixin, GenKeysMixin):
  """Test in_toto_record's main() - requires sys.argv patching; and
  in_toto_record_start/in_toto_record_stop - calls runlib and error logs/exits
  on Exception. """
  cli_main_func = staticmethod(in_toto_record_main)

  @classmethod
  def setUpClass(self):
    """Create and change into temporary directory,
    generate key pair, dummy artifact and base arguments. """
    self.set_up_test_dir()
    self.set_up_gpg_keys()
    self.set_up_keys()

    self.test_artifact1 = "test_artifact1"
    self.test_artifact2 = "test_artifact2"
    open(self.test_artifact1, "w").close()
    open(self.test_artifact2, "w").close()


  @classmethod
  def tearDownClass(self):
    self.tear_down_test_dir()


  def test_start_stop(self):
    """Test CLI command record start/stop with various arguments. """

    # Start/stop recording using rsa key
    args = ["--step-name", "test1", "--key", self.rsa_key_path]
    self.assert_cli_sys_exit(["start"] + args, 0)
    self.assert_cli_sys_exit(["stop"] + args, 0)

    # Start/stop recording using encrypted rsa key with password on prompt
    args = ["--step-name", "test1.1", "--key", self.rsa_key_enc_path,
        "--password"]
    with mock.patch('securesystemslib.interface.get_password',
        return_value=self.key_pw):
      self.assert_cli_sys_exit(["start"] + args, 0)
      self.assert_cli_sys_exit(["stop"] + args, 0)

    # Start/stop recording using encrypted rsa key passing the pw
    args = ["--step-name", "test1.2", "--key", self.rsa_key_enc_path,
        "--password", self.key_pw]
    self.assert_cli_sys_exit(["start"] + args, 0)
    self.assert_cli_sys_exit(["stop"] + args, 0)


    # Start/stop with recording one artifact using rsa key
    args = ["--step-name", "test2", "--key", self.rsa_key_path]
    self.assert_cli_sys_exit(["start"] + args + ["--materials",
      self.test_artifact1], 0)
    self.assert_cli_sys_exit(["stop"] + args + ["--products",
      self.test_artifact1], 0)

    # Start/stop with excluding one artifact using rsa key
    args = ["--step-name", "test2.5", "--key", self.rsa_key_path]
    self.assert_cli_sys_exit(["start"] + args + ["--materials",
      self.test_artifact1, "--exclude", "test*"], 0)
    self.assert_cli_sys_exit(["stop"] + args + ["--products",
      self.test_artifact1, "--exclude", "test*"], 0)

    # Start/stop with base-path using rsa key
    args = ["--step-name", "test2.6", "--key", self.rsa_key_path, "--base-path",
      self.test_dir]
    self.assert_cli_sys_exit(["start"] + args, 0)
    self.assert_cli_sys_exit(["stop"] + args, 0)

    # Start/stop with recording multiple artifacts using rsa key
    args = ["--step-name", "test3", "--key", self.rsa_key_path]
    self.assert_cli_sys_exit(["start"] + args + ["--materials",
      self.test_artifact1, self.test_artifact2], 0)
    self.assert_cli_sys_exit(["stop"] + args + ["--products",
      self.test_artifact2, self.test_artifact2], 0)

    # Start/stop recording using ed25519 key
    args = ["--step-name", "test4", "--key", self.ed25519_key_path, "--key-type", "ed25519"]
    self.assert_cli_sys_exit(["start"] + args, 0)
    self.assert_cli_sys_exit(["stop"] + args, 0)

    # Start/stop with encrypted ed25519 key entering password on the prompt
    args = ["--step-name", "test4.1", "--key", self.ed25519_key_enc_path,
        "--key-type", "ed25519", "--password"]
    with mock.patch('securesystemslib.interface.get_password',
        return_value=self.key_pw):
      self.assert_cli_sys_exit(["start"] + args, 0)
      self.assert_cli_sys_exit(["stop"] + args, 0)

    # Start/stop with encrypted ed25519 key passing the password
    args = ["--step-name", "test4.2", "--key", self.ed25519_key_enc_path,
        "--key-type", "ed25519", "--password", self.key_pw]
    self.assert_cli_sys_exit(["start"] + args, 0)
    self.assert_cli_sys_exit(["stop"] + args, 0)

    # Start/stop with recording one artifact using ed25519 key
    args = ["--step-name", "test5", "--key", self.ed25519_key_path, "--key-type", "ed25519"]
    self.assert_cli_sys_exit(["start"] + args + ["--materials",
      self.test_artifact1], 0)
    self.assert_cli_sys_exit(["stop"] + args + ["--products",
      self.test_artifact1], 0)

    # Start/stop with excluding one artifact using ed25519 key
    args = ["--step-name", "test5.5", "--key", self.ed25519_key_path, "--key-type", "ed25519"]
    self.assert_cli_sys_exit(["start"] + args + ["--materials",
      self.test_artifact1, "--exclude", "test*"], 0)
    self.assert_cli_sys_exit(["stop"] + args + ["--products",
      self.test_artifact1, "--exclude", "test*"], 0)

    # Start/stop with base-path using ed25519 key
    args = ["--step-name", "test5.6", "--key", self.ed25519_key_path,
      "--key-type", "ed25519", "--base-path", self.test_dir]
    self.assert_cli_sys_exit(["start"] + args, 0)
    self.assert_cli_sys_exit(["stop"] + args, 0)

    # Start/stop with recording multiple artifacts using ed25519 key
    args = ["--step-name", "test6", "--key", self.ed25519_key_path, "--key-type", "ed25519"]
    self.assert_cli_sys_exit(["start"] + args + ["--materials",
      self.test_artifact1, self.test_artifact2], 0)
    self.assert_cli_sys_exit(["stop"] + args + ["--products",
      self.test_artifact2, self.test_artifact2], 0)

    # Start/stop sign with specified gpg keyid
    args = ["--step-name", "test7", "--gpg", self.gpg_key_768C43, "--gpg-home",
      self.gnupg_home]
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
    """Test record stop with missing unfinished files when globbing (gpg). """
    args = ["--step-name", "test-no-glob", "--gpg", self.gpg_key_768C43,
        "--gpg-home", self.gnupg_home]
    self.assert_cli_sys_exit(["stop"] + args, 1)

  def test_glob_to_many_unfinished_files(self):
    """Test record stop with to many unfinished files when globbing (gpg). """
    name = "test-to-many-glob"
    fn1 = UNFINISHED_FILENAME_FORMAT.format(step_name=name, keyid="a12345678")
    fn2 = UNFINISHED_FILENAME_FORMAT.format(step_name=name, keyid="b12345678")
    open(fn1, "w").close()
    open(fn2, "w").close()
    args = ["--step-name", name, "--gpg", self.gpg_key_768C43,
        "--gpg-home", self.gnupg_home]
    self.assert_cli_sys_exit(["stop"] + args, 1)

  def test_encrypted_key_but_no_pw(self):
    args = ["--step-name", "enc-key", "--key", self.rsa_key_enc_path]
    self.assert_cli_sys_exit(["start"] + args, 1)
    self.assert_cli_sys_exit(["stop"] + args, 1)

    args = ["--step-name", "enc-key", "--key", self.ed25519_key_enc_path,
        "--key-type", "ed25519"]
    self.assert_cli_sys_exit(["start"] + args, 1)
    self.assert_cli_sys_exit(["stop"] + args, 1)


  def test_wrong_key(self):
    """Test CLI command record with wrong key exits 1 """
    args = ["--step-name", "wrong-key", "--key", "non-existing-key"]
    self.assert_cli_sys_exit(["start"] + args, 1)
    self.assert_cli_sys_exit(["stop"] + args, 1)

  def test_no_key(self):
    """Test if no key is specified, argparse error exists with 2"""
    args = ["--step-name", "no-key"]
    self.assert_cli_sys_exit(["start"] + args, 2)
    self.assert_cli_sys_exit(["stop"] + args, 2)


  def test_missing_unfinished_link(self):
    """Error exit with missing unfinished link file. """
    args = ["--step-name", "no-link", "--key", self.rsa_key_path]
    self.assert_cli_sys_exit(["stop"] + args, 1)

    args = ["--step-name", "no-link", "--key", self.ed25519_key_path, "--key-type", "ed25519"]
    self.assert_cli_sys_exit(["stop"] + args, 1)


if __name__ == '__main__':
  unittest.main()
