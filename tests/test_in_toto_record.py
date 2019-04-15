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

import os
import sys
import unittest
import shutil
import tempfile

if sys.version_info >= (3, 3):
  import unittest.mock as mock # pylint: disable=no-name-in-module,import-error
else:
  import mock # pylint: disable=import-error

import in_toto.util
from in_toto.models.link import UNFINISHED_FILENAME_FORMAT
from in_toto.in_toto_record import main as in_toto_record_main

import tests.common

WORKING_DIR = os.getcwd()



class TestInTotoRecordTool(tests.common.CliTestCase):
  """Test in_toto_record's main() - requires sys.argv patching; and
  in_toto_record_start/in_toto_record_stop - calls runlib and error logs/exits
  on Exception. """
  cli_main_func = staticmethod(in_toto_record_main)

  @classmethod
  def setUpClass(self):
    """Create and change into temporary directory,
    generate key pair, dummy artifact and base arguments. """
    self.test_dir = tempfile.mkdtemp()

    # Find gpg keyring
    gpg_keyring_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "gpg_keyrings", "rsa")

    os.chdir(self.test_dir)

    # Copy gpg keyring to temp dir
    self.gnupg_home = os.path.join(self.test_dir, "rsa")
    shutil.copytree(gpg_keyring_path, self.gnupg_home)
    self.gpg_keyid = "7b3abb26b97b655ab9296bd15b0bd02e1c768c43"

    self.rsa_key_path = "test_key_rsa"
    in_toto.util.generate_and_write_rsa_keypair(self.rsa_key_path)

    self.ed25519_key_path = "test_key_ed25519"
    in_toto.util.generate_and_write_ed25519_keypair(self.ed25519_key_path)

    self.test_artifact1 = "test_artifact1"
    self.test_artifact2 = "test_artifact2"
    open(self.test_artifact1, "w").close()
    open(self.test_artifact2, "w").close()


  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp test directory. """
    os.chdir(WORKING_DIR)
    shutil.rmtree(self.test_dir)


  def test_start_stop(self):
    """Test CLI command record start/stop with various arguments. """

    # Give wrong password whenever prompted.
    with mock.patch('in_toto.util.prompt_password', return_value='x'):

      # Start/stop recording using rsa key
      args = ["--step-name", "test1", "--key", self.rsa_key_path]
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
      args = ["--step-name", "test7", "--gpg", self.gpg_keyid, "--gpg-home",
          self.gnupg_home]
      self.assert_cli_sys_exit(["start"] + args, 0)
      self.assert_cli_sys_exit(["stop"] + args, 0)

      # Start/stop sign with default gpg keyid
      args = ["--step-name", "test8", "--gpg", "--gpg-home", self.gnupg_home]
      self.assert_cli_sys_exit(["start"] + args, 0)
      self.assert_cli_sys_exit(["stop"] + args, 0)



  def test_glob_no_unfinished_files(self):
    """Test record stop with missing unfinished files when globbing (gpg). """
    args = ["--step-name", "test-no-glob", "--gpg", self.gpg_keyid,
        "--gpg-home", self.gnupg_home]
    self.assert_cli_sys_exit(["stop"] + args, 1)

  def test_glob_to_many_unfinished_files(self):
    """Test record stop with to many unfinished files when globbing (gpg). """
    name = "test-to-many-glob"
    fn1 = UNFINISHED_FILENAME_FORMAT.format(step_name=name, keyid="a12345678")
    fn2 = UNFINISHED_FILENAME_FORMAT.format(step_name=name, keyid="b12345678")
    open(fn1, "w").close()
    open(fn2, "w").close()
    args = ["--step-name", name, "--gpg", self.gpg_keyid,
        "--gpg-home", self.gnupg_home]
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
    # Give wrong password whenever prompted.
    with mock.patch('in_toto.util.prompt_password', return_value='x'):
      self.assert_cli_sys_exit(["stop"] + args, 1)

    args = ["--step-name", "no-link", "--key", self.ed25519_key_path, "--key-type", "ed25519"]
    # Give wrong password whenever prompted.
    with mock.patch('in_toto.util.prompt_password', return_value='x'):
      self.assert_cli_sys_exit(["stop"] + args, 1)


if __name__ == '__main__':
  unittest.main()
