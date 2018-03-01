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
import argparse
import shutil
import tempfile
from mock import patch

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

    self.key_path = "test_key"
    in_toto.util.generate_and_write_rsa_keypair(self.key_path)

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

    # Start/stop recording
    args = ["--step-name", "test1", "--key", self.key_path]
    self.assert_cli_sys_exit(["start"] + args, 0)
    self.assert_cli_sys_exit(["stop"] + args, 0)

    # Start/stop with recording one artifact
    args = ["--step-name", "test2", "--key", self.key_path]
    self.assert_cli_sys_exit(["start"] + args + ["--materials",
        self.test_artifact1], 0)
    self.assert_cli_sys_exit(["stop"] + args + ["--products",
        self.test_artifact1], 0)

    # Start/stop with recording multiple artifacts
    args = ["--step-name", "test3", "--key", self.key_path]
    self.assert_cli_sys_exit(["start"] + args + ["--materials",
        self.test_artifact1, self.test_artifact2], 0)
    self.assert_cli_sys_exit(["stop"] + args + ["--products",
        self.test_artifact2, self.test_artifact2], 0)

    # Start/stop sign with specified gpg keyid
    args = ["--step-name", "test5", "--gpg", self.gpg_keyid, "--gpg-home",
        self.gnupg_home]
    self.assert_cli_sys_exit(["start"] + args, 0)
    self.assert_cli_sys_exit(["stop"] + args, 0)

    # Start/stop sign with default gpg keyid
    args = ["--step-name", "test6", "--gpg", "--gpg-home", self.gnupg_home]
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
    args = ["--step-name", "no-link", "--key", self.key_path]
    self.assert_cli_sys_exit(["stop"] + args, 1)


if __name__ == '__main__':
  unittest.main()
