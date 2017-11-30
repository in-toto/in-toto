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
import logging
import argparse
import shutil
import tempfile
from mock import patch

from in_toto.util import (generate_and_write_rsa_keypair,
    prompt_import_rsa_key_from_file)

from in_toto.models.link import Link
from in_toto.in_toto_run import main as in_toto_run_main
from in_toto.in_toto_run import in_toto_run
from in_toto.models.link import FILENAME_FORMAT

# Suppress all the user feedback that we print using a base logger
logging.getLogger().setLevel(logging.CRITICAL)

class TestInTotoRunTool(unittest.TestCase):
  """Test in_toto_run's main() - requires sys.argv patching; and
  in_toto_run- calls runlib and error logs/exits on Exception. """

  @classmethod
  def setUpClass(self):
    """Create and change into temporary directory,
    generate key pair, dummy artifact and base arguments. """

    self.working_dir = os.getcwd()

    self.test_dir = tempfile.mkdtemp()
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
    try:
      os.remove(self.test_link)
    except OSError:
      pass

  def test_main_required_args(self):
    """Test CLI command with required arguments. """

    args = [ "in_toto_run.py", "--step-name", self.test_step, "--key",
        self.key_path, "--", "echo", "test"]
    with patch.object(sys, 'argv', args):
      in_toto_run_main()

    self.assertTrue(os.path.exists(self.test_link))

  def test_main_optional_args(self):
    """Test CLI command with optional arguments. """

    args = [ "in_toto_run.py", "--step-name", self.test_step, "--key",
        self.key_path, "--materials", self.test_artifact, "--products",
        self.test_artifact, "--record-streams", "--", "echo", "test"]

    with patch.object(sys, 'argv', args):
      in_toto_run_main()

    self.assertTrue(os.path.exists(self.test_link))

  def test_main_no_command_arg(self):
    """Test CLI command with --no-command argument. """

    args = [ "in_toto_run.py", "--step-name", self.test_step, "--key",
        self.key_path, "--no-command"]

    with patch.object(sys, 'argv', args):
      in_toto_run_main()

    self.assertTrue(os.path.exists(self.test_link))

  def test_main_wrong_args(self):
    """Test CLI command with missing arguments. """

    wrong_args_list = [
      ["in_toto_run.py"],
      ["in_toto_run.py", "--step-name", "some"],
      ["in_toto_run.py", "--key", self.key_path],
      ["in_toto_run.py", "--", "echo", "blub"],
      ["in_toto_run.py", "--step-name", "test-step", "--key", self.key_path],
      ["in_toto_run.py", "--step-name", "--", "echo", "blub"],
      ["in_toto_run.py", "--key", self.key_path, "--", "echo", "blub"],
      ["in_toto_run.py", "--step-name", "test-step", "--key", self.key_path, "--"]]

    for wrong_args in wrong_args_list:
      with patch.object(sys, 'argv', wrong_args), self.assertRaises(SystemExit):
        in_toto_run_main()
      self.assertFalse(os.path.exists(self.test_link))

  def test_main_wrong_key_exits(self):
    """Test CLI command with wrong key argument, exits and logs error """

    args = [ "in_toto_run.py", "--step-name", self.test_step, "--key",
       "non-existing-key", "--", "echo", "test"]

    with patch.object(sys, 'argv', args), self.assertRaises(SystemExit):
      in_toto_run_main()
    self.assertFalse(os.path.exists(self.test_link))

  def test_main_verbose(self):
    """Log level with verbose flag is lesser/equal than logging.INFO. """

    args = [ "in_toto_run.py", "--step-name", self.test_step, "--key",
        self.key_path, "--materials", self.test_artifact, "--products",
        self.test_artifact, "--record-streams", "--verbose",
        "--", "echo", "test"]

    original_log_level = logging.getLogger().getEffectiveLevel()
    with patch.object(sys, 'argv', args ):
      in_toto_run_main()
    self.assertTrue(os.path.exists(self.test_link))

    self.assertLessEqual(logging.getLogger().getEffectiveLevel(), logging.INFO)
    # Reset log level
    logging.getLogger().setLevel(original_log_level)

  def test_successful_in_toto_run(self):
    """Call in_toto_run successfully """
    in_toto_run(self.test_step, [self.test_artifact], [self.test_artifact],
        ["echo", "test"], False, self.key, None, False, None)

    self.assertTrue(os.path.exists(self.test_link))

  def test_in_toto_run_bad_key_error_exit(self):
    """Error exit in_toto_run with bad key. """
    with self.assertRaises(SystemExit):
      in_toto_run(self.test_step, [self.test_artifact], [self.test_artifact],
          ["echo", "test"], False, "bad-key", None, False, None)

if __name__ == "__main__":
  unittest.main(buffer=True)
