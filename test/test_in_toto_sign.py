
"""
<Program Name>
  test_in_toto_sign.py
<Author>
  Sachit Malik <i.sachitmalik@gmail.com>
<Started>
  Wed Jun 21, 2017
<Copyright>
  See LICENSE for licensing information.
<Purpose>
  Test in_toto_sign command line tool.
"""

import os
import sys
import unittest
import logging
import argparse
import shutil
import tempfile
from mock import patch
from in_toto.models.layout import Layout
from in_toto.util import (generate_and_write_rsa_keypair,
  prompt_import_rsa_key_from_file)
from in_toto.models.link import Link
from in_toto.in_toto_sign import main as in_toto_sign_main
from in_toto.in_toto_sign import add_sign, replace_sign, verify_sign
from in_toto import log
from in_toto import exceptions
from in_toto.util import import_rsa_key_from_file

WORKING_DIR = os.getcwd()

# Suppress all the user feedback that we print using a base logger
logging.getLogger().setLevel(logging.CRITICAL)

class TestInTotoSignTool(unittest.TestCase):
  """Test in_toto_sign's main() - requires sys.argv patching; error logs/exits
  on Exception. """

  @classmethod
  def setUpClass(self):
     # Backup original cwd
    self.working_dir = os.getcwd()

    # Find demo files
    demo_files = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "demo_files")

    # Create and change into temporary directory
    self.test_dir = os.path.realpath(tempfile.mkdtemp())
    os.chdir(self.test_dir)

    # Copy demo files to temp dir
    for file in os.listdir(demo_files):
      shutil.copy(os.path.join(demo_files, file), self.test_dir)

    # Load layout template
    layout_template = Layout.read_from_file("demo.layout.template")

    # Store layout paths to be used in tests
    self.layout_single_signed_path = "single-signed.layout"
    self.layout_double_signed_path = "double-signed.layout"

    # Import layout signing keys
    alice = import_rsa_key_from_file("alice")
    self.alice_path_pvt = "alice"
    self.alice_path = "alice.pub"

    # dump a single signed layout
    layout_template.sign(alice)
    layout_template.dump(self.layout_single_signed_path)

  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp dir. """
    os.chdir(self.working_dir)
    shutil.rmtree(self.test_dir)

  def test_main_required_args(self):
    """Test in-toto-sign CLI tool with required arguments. """
    args = ["in_toto_sign.py"]

    with patch.object(sys, 'argv', args + ["sign" , "--key",
      self.alice_path_pvt, self.layout_single_signed_path]), \
         self.assertRaises(SystemExit):
        in_toto_sign_main()

    with patch.object(sys, 'argv', args + ["verify" , "--key",
      self.alice_path, self.layout_single_signed_path]):
       in_toto_sign_main()


  def test_main_optional_args(self):
    """Test CLI command sign with optional arguments. """
    args = ["in_toto_sign.py"]

    with patch.object(sys, 'argv', args + ["sign", "--key",
      self.alice_path_pvt, "-r", self.layout_single_signed_path]),\
      self.assertRaises(SystemExit):
          in_toto_sign_main()

    with patch.object(sys, 'argv', args + ["sign", "--key",
      self.alice_path_pvt, "-i", self.layout_single_signed_path]),\
         self.assertRaises(SystemExit):
        in_toto_sign_main()

    with patch.object(sys, 'argv', args + ["sign", "--key",
      self.alice_path_pvt, self.layout_single_signed_path]),\
         self.assertRaises(SystemExit):
        in_toto_sign_main()


  def test_main_wrong_args(self):
    """Test CLI command record start/stop with missing arguments. """

    wrong_args_list = [
      ["in_toto_sign.py"],
      ["in_toto_sign.py", "random"],
      ["in_toto_sign.py", "sign", "--key", self.alice_path],
      ["in_toto_sign.py", "verify", "--key", self.alice_path_pvt],
    ]

    for wrong_args in wrong_args_list:
      with patch.object(sys, 'argv', wrong_args), self.assertRaises(
        SystemExit):
        in_toto_sign_main()

  def test_main_wrong_key_exits(self):
    """Test CLI command record with wrong key exits and logs error """
    args = ["in_toto_sign.py"]
    with patch.object(sys, 'argv', args + ["sign" , "--key",
      "non-existent-key", "-r", "-i", self.layout_single_signed_path]), \
      self.assertRaises(IOError):
      in_toto_sign_main()

    with patch.object(sys, 'argv', args + ["verify" , "--key",
      "non-existent-key", self.layout_single_signed_path]), \
      self.assertRaises(IOError):
      in_toto_sign_main()

  def test_main_verbose(self):
    """Log level with verbose flag is lesser/equal than logging.INFO. """
    args = ["in_toto_sign.py"]

    original_log_level = logging.getLogger().getEffectiveLevel()
    with patch.object(sys, 'argv', args + ["sign", "--key",
      self.alice_path_pvt , "-r", "-i", "--verbose",
      self.layout_single_signed_path]):
      in_toto_sign_main()

    with patch.object(sys, 'argv', args + ["verify", "--key",
      self.alice_path, "--verbose", self.layout_single_signed_path]):
      in_toto_sign_main()

    self.assertLessEqual(logging.getLogger().getEffectiveLevel(), logging.INFO)

    # Reset log level
    logging.getLogger().setLevel(original_log_level)

  def test_in_toto_sign_add_sign(self):
    """in_toto_sign_add_sign run through. """
    add_sign(self.layout_single_signed_path, self.alice_path_pvt)

  def test_in_toto_sign_replace_sign(self):
    """in_toto_sign_replace_sign run through. """
    replace_sign(self.layout_single_signed_path, self.alice_path_pvt)

  def test_in_toto_sign_verify_sign(self):
    """in_toto_sign_verify_sign run through. """
    with assertRaises(exceptions.SignatureVerificationError):
      verify_sign(self.layout_single_signed_path, self.alice_path)


  def test_add_sign_bad_key_error_exit(self):
    """Error exit in_toto_add_sign with bad key. """
    with self.assertRaises(IOError):
      add_sign(self.layout_single_signed_path, "bad-key")

  def test_verify_sign_bad_key_error_exit(self):
    """Error exit in_toto_verify_sign with bad key. """
    with self.assertRaises(IOError):
      verify_sign(self.layout_single_signed_path, "bad-key")



if __name__ == '__main__':
  unittest.main(buffer=True)