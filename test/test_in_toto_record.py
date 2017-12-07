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
import logging
import argparse
import shutil
import tempfile
from mock import patch

from in_toto.util import (generate_and_write_rsa_keypair,
    prompt_import_rsa_key_from_file)
from in_toto.models.link import Link
from in_toto.in_toto_record import main as in_toto_record_main

WORKING_DIR = os.getcwd()

# Suppress all the user feedback that we print using a base logger
logging.getLogger().setLevel(logging.CRITICAL)

class TestInTotoRecordTool(unittest.TestCase):
  """Test in_toto_record's main() - requires sys.argv patching; and
  in_toto_record_start/in_toto_record_stop - calls runlib and error logs/exits
  on Exception. """

  @classmethod
  def setUpClass(self):
    """Create and change into temporary directory,
    generate key pair, dummy artifact and base arguments. """
    self.test_dir = tempfile.mkdtemp()
    os.chdir(self.test_dir)

    self.key_path = "test_key"
    generate_and_write_rsa_keypair(self.key_path)
    self.key = prompt_import_rsa_key_from_file(self.key_path)

    self.test_artifact = "test_artifact"
    open(self.test_artifact, "w").close()

  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp test directory. """
    os.chdir(WORKING_DIR)
    shutil.rmtree(self.test_dir)

  def test_main_required_args(self):
    """Test CLI command record start/stop with required arguments. """
    args = [ "in_toto_record.py", "--step-name", "test-step", "--key",
        self.key_path]
    with patch.object(sys, 'argv', args + ["start"]):
      in_toto_record_main()
    with patch.object(sys, 'argv', args + ["stop"]):
      in_toto_record_main()

  def test_main_optional_args(self):
    """Test CLI command record start/stop with optional arguments. """
    args = [ "in_toto_record.py", "--step-name", "test-step", "--key",
        self.key_path]
    with patch.object(sys, 'argv', args + ["start", "--materials",
        self.test_artifact]):
      in_toto_record_main()
    with patch.object(sys, 'argv', args + ["stop", "--products",
        self.test_artifact]):
      in_toto_record_main()

  def test_main_wrong_args(self):
    """Test CLI command record start/stop with missing arguments. """

    wrong_args_list = [
      ["in_toto_record.py"],
      ["in_toto_record.py", "--step-name", "some"],
      ["in_toto_record.py", "--key", self.key_path],
      ["in_toto_record.py", "--step-name", "test-step", "--key",
        self.key_path, "start", "--products"],
      ["in_toto_record.py", "--step-name", "test-step", "--key",
        self.key_path, "stop", "--materials"]
    ]

    for wrong_args in wrong_args_list:
      with patch.object(sys, 'argv',
          wrong_args), self.assertRaises(SystemExit):
        in_toto_record_main()

  def test_main_wrong_key_exits(self):
    """Test CLI command record with wrong key exits and logs error """
    args = [ "in_toto_record.py", "--step-name", "test-step", "--key",
        "non-existing-key", "start"]
    with patch.object(sys, 'argv',
        args), self.assertRaises(
        SystemExit):
      in_toto_record_main()

  def test_main_verbose(self):
    """Log level with verbose flag is lesser/equal than logging.INFO. """
    args = [ "in_toto_record.py", "--step-name", "test-step", "--key",
        self.key_path, "--verbose"]

    original_log_level = logging.getLogger().getEffectiveLevel()
    with patch.object(sys, 'argv', args + ["start"]):
      in_toto_record_main()
    with patch.object(sys, 'argv', args + ["stop"]):
      in_toto_record_main()
    self.assertLessEqual(logging.getLogger().getEffectiveLevel(), logging.INFO)
    # Reset log level
    logging.getLogger().setLevel(original_log_level)

  def test_stop_missing_unfinished_link_exit(self):
    """Error exit with missing unfinished link file. """
    args = ["in_toto_record.py", "-n", "test-step", "-k", self.key_path, "stop"]
    with patch.object(sys, 'argv', args), self.assertRaises(SystemExit):
      in_toto_record_main()


if __name__ == '__main__':
  unittest.main(buffer=True)
