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

import in_toto.util
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

  def _test_cli_sys_exit(self, cli_args, status):
    """Test helper to mock command line call and assert return value. """
    with patch.object(sys, "argv", ["in_toto_record.py"]
        + cli_args), self.assertRaises(SystemExit) as raise_ctx:
      in_toto_record_main()
    self.assertEqual(raise_ctx.exception.code, status)


  def test_start_stop(self):
    """Test CLI command record start/stop with various arguments. """

    # Start/stop recording
    args = ["--step-name", "test1", "--key", self.key_path]
    self._test_cli_sys_exit(["start"] + args, 0)
    self._test_cli_sys_exit(["stop"] + args, 0)

    # Start/stop with recording one artifact
    args = ["--step-name", "test2", "--key", self.key_path]
    self._test_cli_sys_exit(["start"] + args + ["--materials",
        self.test_artifact1], 0)
    self._test_cli_sys_exit(["stop"] + args + ["--products",
        self.test_artifact1], 0)

    # Start/stop with recording multiple artifacts
    args = ["--step-name", "test3", "--key", self.key_path]
    self._test_cli_sys_exit(["start"] + args + ["--materials",
        self.test_artifact1, self.test_artifact2], 0)
    self._test_cli_sys_exit(["stop"] + args + ["--products",
        self.test_artifact2, self.test_artifact2], 0)

    # Start/stop recording verbosely
    args = ["--step-name", "test4", "--key", self.key_path, "--verbose"]
    self._test_cli_sys_exit(["start"] + args, 0)
    self._test_cli_sys_exit(["stop"] + args, 0)


  def test_no_key(self):
    """Test CLI command record with wrong key exits 1 """
    args = ["--step-name", "no-key", "--key", "non-existing-key"]
    self._test_cli_sys_exit(["start"] + args, 1)
    self._test_cli_sys_exit(["stop"] + args, 1)


  def test_missing_unfinished_link(self):
    """Error exit with missing unfinished link file. """
    args = ["--step-name", "no-link", "--key", self.key_path]
    self._test_cli_sys_exit(["stop"] + args, 1)


if __name__ == '__main__':
  unittest.main(buffer=True)
