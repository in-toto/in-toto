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
import sys
import unittest
if sys.version_info >= (3, 3):
  from unittest.mock import patch # pylint: disable=no-name-in-module,import-error
else:
  from mock import patch # pylint: disable=import-error

from in_toto.in_toto_keygen import main as in_toto_keygen_main

from tests.common import TmpDirMixin


class TestInTotoKeyGenTool(unittest.TestCase, TmpDirMixin):
  """Test in_toto_keygen's main() - requires sys.argv patching; error
  logs/exits on Exception. """

  @classmethod
  def setUpClass(self):
    self.set_up_test_dir()

  @classmethod
  def tearDownClass(self):
    self.tear_down_test_dir()

  def test_main_required_args(self):
    """Test in-toto-keygen CLI tool with required arguments. """
    args = ["in_toto_keygen.py"]

    with patch.object(sys, 'argv', args + ["bob"]), \
      self.assertRaises(SystemExit):
      in_toto_keygen_main()


  def test_main_optional_args(self):
    """Test CLI command keygen with optional arguments. """
    args = ["in_toto_keygen.py"]
    password = "123456"
    with patch.object(sys, 'argv', args + ["-p", "bob"]), \
      patch("getpass.getpass", return_value=password), self.assertRaises(
      SystemExit):
      in_toto_keygen_main()
    with patch.object(sys, 'argv', args + ["-p", "-t", "rsa", "bob"]), \
      patch("getpass.getpass", return_value=password), self.assertRaises(
      SystemExit):
      in_toto_keygen_main()
    with patch.object(sys, 'argv', args + ["-t", "ed25519", "bob"]), \
      self.assertRaises(SystemExit):
      in_toto_keygen_main()
    with patch.object(sys, 'argv', args + ["-p", "-t", "ed25519", "bob"]), \
      patch("getpass.getpass", return_value=password), self.assertRaises(
      SystemExit):
      in_toto_keygen_main()
    with patch.object(sys, 'argv', args + ["-p", "-b", "3072", "bob"]), \
      patch("getpass.getpass", return_value=password), self.assertRaises(
      SystemExit):
      in_toto_keygen_main()


  def test_main_wrong_args(self):
    """Test CLI command with missing arguments. """
    wrong_args_list = [
      ["in_toto_keygen.py"],
      ["in_toto_keygen.py", "-r"],
      ["in_toto_keygen.py", "-p", "-b", "1024", "bob"]]
    password = "123456"

    for wrong_args in wrong_args_list:
      with patch.object(sys, 'argv', wrong_args), patch("getpass.getpass",
        return_value=password), self.assertRaises(SystemExit):
        in_toto_keygen_main()

if __name__ == '__main__':
  unittest.main()
