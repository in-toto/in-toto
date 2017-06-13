#!/usr/bin/env python

"""
<Program Name>
  test_in_toto_mock.py

<Author>
  Shikher Verma <root@shikherverma.com>

<Started>
  June 12, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test in_toto_mock command line tool.

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
from in_toto.in_toto_mock import main as in_toto_mock_main
from in_toto.in_toto_mock import in_toto_mock
from in_toto.models.link import MOCK_FILENAME_FORMAT

# Suppress all the user feedback that we print using a base logger
logging.getLogger().setLevel(logging.CRITICAL)

class TestInTotoMockTool(unittest.TestCase):
  """Test in_toto_mock's main() - requires sys.argv patching; and
  in_toto_mock- calls runlib and error logs/exits on Exception. """

  @classmethod
  def setUpClass(self):
    """Create and change into temporary directory,
    dummy artifact and base arguments. """

    self.working_dir = os.getcwd()

    self.test_dir = tempfile.mkdtemp()
    os.chdir(self.test_dir)

    self.test_step = "test_step"
    self.test_link = MOCK_FILENAME_FORMAT.format(step_name=self.test_step)
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

    args = [ "in_toto_mock.py", "--name", self.test_step, "--", "echo", "test"]
    with patch.object(sys, 'argv', args):
      in_toto_mock_main()

    self.assertTrue(os.path.exists(self.test_link))

  def test_main_optional_args(self):
    """Test CLI command with optional arguments. """

    args = [ "in_toto_mock.py", "--name", self.test_step, "--materials",
        self.test_artifact, "--products", self.test_artifact,
        "--record-byproducts", "--", "echo", "test"]

    with patch.object(sys, 'argv', args):
      in_toto_mock_main()

    self.assertTrue(os.path.exists(self.test_link))

  def test_main_wrong_args(self):
    """Test CLI command with missing arguments. """

    wrong_args_list = [
      ["in_toto_mock.py"],
      ["in_toto_mock.py", "--name", "test-step"],
      ["in_toto_mock.py", "--", "echo", "blub"],
      ["in_toto_record.py", "--", "echo", "blub"]]

    for wrong_args in wrong_args_list:
      with patch.object(sys, 'argv', wrong_args), self.assertRaises(SystemExit):
        in_toto_mock_main()
      self.assertFalse(os.path.exists(self.test_link))

  def test_main_verbose(self):
    """Log level with verbose flag is lesser/equal than logging.INFO. """

    args = [ "in_toto_mock.py", "--name", self.test_step, "--materials",
        self.test_artifact, "--products",
        self.test_artifact, "--record-byproducts", "--verbose",
        "--", "echo", "test"]

    original_log_level = logging.getLogger().getEffectiveLevel()
    with patch.object(sys, 'argv', args ):
      in_toto_mock_main()
    self.assertTrue(os.path.exists(self.test_link))

    self.assertLessEqual(logging.getLogger().getEffectiveLevel(), logging.INFO)
    # Reset log level
    logging.getLogger().setLevel(original_log_level)

  def test_successful_in_toto_mock(self):
    """Call in_toto_mock successfully """
    in_toto_mock(self.test_step, [self.test_artifact],
      [self.test_artifact], ["echo", "test"], True)

    self.assertTrue(os.path.exists(self.test_link))

if __name__ == "__main__":
  unittest.main(buffer=True)
