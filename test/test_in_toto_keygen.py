"""
<Program Name>
  test_in_toto_keygen.py
<Author>
  Sachit Malik <i.sachitmalik@gmail.com>
<Started>
  Wed Jun 28, 2017
<Copyright>
  See LICENSE for licensing information.
<Purpose>
  Test in_toto_keygen command line tool.
"""

import os
import sys
import unittest
import logging
import argparse
import shutil
import tempfile
from mock import patch
from in_toto.in_toto_keygen import main as in_toto_keygen_main
from in_toto.in_toto_keygen import generate_and_write_rsa_keypair, \
    prompt_generate_and_write_rsa_keypair
from in_toto import log
from in_toto import exceptions

WORKING_DIR = os.getcwd()

# Suppress all the user feedback that we print using a base logger
logging.getLogger().setLevel(logging.CRITICAL)

class TestInTotoKeyGenTool(unittest.TestCase):
  """Test in_toto_keygen's main() - requires sys.argv patching; error
  logs/exits on Exception. """

  @classmethod
  def setUpClass(self):
    # Create directory where the verification will take place
    self.working_dir = os.getcwd()
    self.test_dir = os.path.realpath(tempfile.mkdtemp())
    os.chdir(self.test_dir)

  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp test directory. """
    os.chdir(self.working_dir)
    shutil.rmtree(self.test_dir)

  def test_main_required_args(self):
    """Test in-toto-keygen CLI tool with required arguments. """
    args = ["in_toto_keygen.py"]

    with patch.object(sys, 'argv', args + ["bob"]), \
      self.assertRaises(SystemExit):
      in_toto_keygen_main()


  def test_main_optional_args(self):
    """Test CLI command keygen with optional arguments. """
    args = ["in_toto_keygen.py"]

    with patch.object(sys, 'argv', args + ["-p", "bob"]), \
      self.assertRaises(SystemExit):
      in_toto_keygen_main()


  def test_main_wrong_args(self):
    """Test CLI command with missing arguments. """
    wrong_args_list = [
      ["in_toto_keygen.py"],
      ["in_toto_keygen.py", "-p"]]

    for wrong_args in wrong_args_list:
      with patch.object(sys, 'argv', wrong_args), self.assertRaises(
        SystemExit):
        in_toto_keygen_main()

  def test_in_toto_keygen_generate_and_write_rsa_keypair(self):
    """in_toto_keygen_generate_and_write_rsa_keypair run through. """
    generate_and_write_rsa_keypair("bob")

  def test_in_toto_keygen_prompt_generate_and_write_rsa_keypair(self):
    """in_toto_keygen_prompt_generate_and_write_rsa_keypair run through. """
    prompt_generate_and_write_rsa_keypair("bob")


if __name__ == '__main__':
  unittest.main(buffer=True)