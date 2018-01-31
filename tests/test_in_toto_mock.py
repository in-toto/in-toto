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
import argparse
import shutil
import tempfile
from mock import patch

from in_toto.in_toto_mock import main as in_toto_mock_main
from in_toto.in_toto_mock import in_toto_mock

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
    self.test_link = self.test_step + ".link"
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

  def test_main_wrong_args(self):
    """Test CLI command with missing arguments. """

    wrong_args_list = [
      ["in_toto_mock.py"],
      ["in_toto_mock.py", "--name", "test-step"],
      ["in_toto_mock.py", "--", "echo", "blub"]]

    for wrong_args in wrong_args_list:
      with patch.object(sys, 'argv', wrong_args), self.assertRaises(SystemExit):
        in_toto_mock_main()
      self.assertFalse(os.path.exists(self.test_link))

  def test_successful_in_toto_mock(self):
    """Call in_toto_mock successfully """
    in_toto_mock(self.test_step, ["echo", "test"])

    self.assertTrue(os.path.exists(self.test_link))

  def test_in_toto_run_bad_command_exit(self):
    """Error exit in_toto_mock for bad command. """
    with self.assertRaises(SystemExit):
      in_toto_mock(self.test_step, ["exit", "1"])

if __name__ == "__main__":
  unittest.main()
