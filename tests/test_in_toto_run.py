#!/usr/bin/env python

"""
<Program Name>
  test_in_toto_run.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Nov 28, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test in_toto_run command line tool.

"""

import os
import sys
import unittest
import argparse
import shutil
import glob
import tempfile
from mock import patch

from in_toto.util import (generate_and_write_rsa_keypair,
    prompt_import_rsa_key_from_file)

from in_toto.models.link import Link
from in_toto.in_toto_run import main as in_toto_run_main
from in_toto.models.link import FILENAME_FORMAT

import in_toto.gpg.util
import tests.common



class TestInTotoRunTool(tests.common.CliTestCase):
  """Test in_toto_run's main() - requires sys.argv patching; and
  in_toto_run- calls runlib and error logs/exits on Exception. """
  cli_main_func = staticmethod(in_toto_run_main)

  @classmethod
  def setUpClass(self):
    """Create and change into temporary directory,
    generate key pair, dummy artifact and base arguments. """

    self.working_dir = os.getcwd()

    self.test_dir = tempfile.mkdtemp()

    # Copy gpg keyring
    self.default_gpg_keyid = "8465a1e2e0fb2b40adb2478e18fb3f537e0c8a17"
    self.default_gpg_subkeyid = "c5a0abe6ec19d0d65f85e2c39be9df5131d924e9"
    self.non_default_gpg_keyid = "8288ef560ed3795f9df2c0db56193089b285da58"
    gpg_keyring_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "gpg_keyrings", "rsa")
    self.gnupg_home = os.path.join(self.test_dir, "rsa")
    shutil.copytree(gpg_keyring_path, self.gnupg_home)

    os.chdir(self.test_dir)

    self.key_path = "test_key"
    generate_and_write_rsa_keypair(self.key_path)
    self.key = prompt_import_rsa_key_from_file(self.key_path)

    self.test_step = "test_step"
    self.test_link = FILENAME_FORMAT.format(step_name=self.test_step, keyid=self.key["keyid"])
    self.test_artifact = "test_artifact"
    open(self.test_artifact, "w").close()

  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp test directory. """
    os.chdir(self.working_dir)
    shutil.rmtree(self.test_dir)

  def tearDown(self):
    for link in glob.glob("*.link"):
      os.remove(link)

  def test_main_required_args(self):
    """Test CLI command with required arguments. """

    args = ["--step-name", self.test_step, "--key", self.key_path, "--",
        "echo", "test"]

    self.assert_cli_sys_exit(args, 0)
    self.assertTrue(os.path.exists(self.test_link))


  def test_main_optional_args(self):
    """Test CLI command with optional arguments. """

    args = ["--step-name", self.test_step, "--key",
        self.key_path, "--materials", self.test_artifact, "--products",
        self.test_artifact, "--record-streams", "--", "echo", "test"]

    self.assert_cli_sys_exit(args, 0)
    self.assertTrue(os.path.exists(self.test_link))


  def test_main_with_specified_gpg_key(self):
    """Test CLI command with specified gpg key. """
    args = ["-n", self.test_step,
            "--gpg", self.non_default_gpg_keyid,
            "--gpg-home", self.gnupg_home, "--", "ls"]

    self.assert_cli_sys_exit(args, 0)
    link_filename = FILENAME_FORMAT.format(step_name=self.test_step,
        keyid=self.non_default_gpg_keyid)

    self.assertTrue(os.path.exists(link_filename))


  def test_main_with_default_gpg_key(self):
    """Test CLI command with default gpg key. """
    args = ["-n", self.test_step,
            "--gpg", "--gpg-home", self.gnupg_home, "--", "ls"]

    self.assert_cli_sys_exit(args, 0)

    link_filename = FILENAME_FORMAT.format(step_name=self.test_step,
        keyid=self.default_gpg_subkeyid)

    self.assertTrue(os.path.exists(link_filename))


  def test_main_no_command_arg(self):
    """Test CLI command with --no-command argument. """

    args = [ "in_toto_run.py", "--step-name", self.test_step, "--key",
        self.key_path, "--no-command"]

    self.assert_cli_sys_exit(args, 0)
    self.assertTrue(os.path.exists(self.test_link))

  def test_main_wrong_args(self):
    """Test CLI command with missing arguments. """

    wrong_args_list = [
      [],
      ["--step-name", "some"],
      ["--key", self.key_path],
      ["--", "echo", "blub"],
      ["--step-name", "test-step", "--key", self.key_path],
      ["--step-name", "--", "echo", "blub"],
      ["--key", self.key_path, "--", "echo", "blub"],
      ["--step-name", "test-step", "--key", self.key_path, "--"],
      ["--step-name", "test-step",
          "--key", self.key_path, "--gpg", "--", "echo", "blub"]
    ]

    for wrong_args in wrong_args_list:
      self.assert_cli_sys_exit(wrong_args, 2)
      self.assertFalse(os.path.exists(self.test_link))

  def test_main_wrong_key_exits(self):
    """Test CLI command with wrong key argument, exits and logs error """

    args = ["--step-name", self.test_step, "--key",
       "non-existing-key", "--", "echo", "test"]

    self.assert_cli_sys_exit(args, 1)
    self.assertFalse(os.path.exists(self.test_link))


if __name__ == "__main__":
  unittest.main()
