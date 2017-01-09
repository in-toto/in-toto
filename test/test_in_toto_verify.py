#!/usr/bin/env python

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
import sys
import unittest
import logging
import argparse
import shutil
import tempfile
from mock import patch

from in_toto.models.link import Link
from in_toto.in_toto_verify import main as in_toto_verify_main
from in_toto.in_toto_verify import in_toto_verify
from in_toto import log
from in_toto import exceptions


# Suppress all the user feedback that we print using a base logger
logging.getLogger().setLevel(logging.CRITICAL)

class TestInTotoVerifyTool(unittest.TestCase):
  """Test
  - in_toto_verify's main() - requires sys.argv patching;
  - in_toto_verify - calls verifylib.in_toto_verify and error logs/exits
    on Exception. """

  @classmethod
  def setUpClass(self):
    """Create and change into temporary directory. """

    self.working_dir = os.getcwd()
    test_base_dir = os.path.dirname(os.path.realpath(__file__))

    self.demo_pass_path = os.path.join(test_base_dir, "demo_pass")
    self.demo_fail_path = os.path.join(test_base_dir, "demo_fail")
    self.layout_path = "root.layout"
    self.layout_double_signed_path = "root-double-signed.layout"
    self.alice_path = "alice.pub"
    self.bob_path = "bob.pub"

    self.test_dir = os.path.realpath(tempfile.mkdtemp())
    os.chdir(self.test_dir)

  def tearDown(self):
    """Remove files from temp dir after every test. """
    for file in os.listdir("."):
      os.remove(file)

  def copyTestFiles(self, from_path):
    for file in os.listdir(from_path):
      shutil.copy(os.path.join(from_path, file), self.test_dir)

  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp test directory. """
    os.chdir(self.working_dir)
    shutil.rmtree(self.test_dir)

  def test_main_required_args(self):
    """Test CLI command successful verify with required arguments. """
    self.copyTestFiles(self.demo_pass_path)
    args = [ "in-toto-verify", "--layout", self.layout_path, "--layout-keys",
        self.alice_path]

    with patch.object(sys, 'argv', args):
      in_toto_verify_main()

  def test_main_wrong_args(self):
    """Test CLI command verify with wrong arguments. """
    wrong_args_list = [
      ["in-toto-verify"],
      ["in-toto-verify", "--layout", self.layout_path],
      ["in-toto-verify", "--key", self.alice_path],
    ]

    for wrong_args in wrong_args_list:
      with patch.object(sys, 'argv', wrong_args), self.assertRaises(SystemExit):
        in_toto_verify_main()

  def test_main_multiple_keys(self):
    """Test """
    self.copyTestFiles(self.demo_pass_path)
    args = [ "in-toto-verify", "--layout", self.layout_double_signed_path,
        "--layout-keys", self.alice_path, self.bob_path]
    with patch.object(sys, 'argv', args):
      in_toto_verify_main()

  def test_main_verbose(self):
    """Log level with verbose flag is lesser/equal than logging.INFO. """
    self.copyTestFiles(self.demo_pass_path)
    args = [ "in-toto-verify", "--layout", self.layout_path, "--layout-keys",
        self.alice_path, "--verbose"]

    original_log_level = logging.getLogger().getEffectiveLevel()
    with patch.object(sys, 'argv', args):
      in_toto_verify_main()
    self.assertLessEqual(logging.getLogger().getEffectiveLevel(), logging.INFO)
    # Reset log level
    logging.getLogger().setLevel(original_log_level)

  def test_in_toto_verify_pass_all(self):
    """in_toto_record_verify run through. """
    self.copyTestFiles(self.demo_pass_path)
    in_toto_verify(self.layout_path, [self.alice_path])

  def test_in_toto_verify_fail(self):
    """in_toto_record_verify fail. """

    self.copyTestFiles(self.demo_fail_path)

    with self.assertRaises(SystemExit):
      in_toto_verify(self.layout_path, [self.alice_path])

if __name__ == "__main__":
  unittest.main(buffer=True)
