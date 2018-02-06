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
import argparse
import shutil
import tempfile
from mock import patch

from in_toto.models.link import Link
from in_toto.models.layout import Layout
from in_toto.models.metadata import Metablock
from in_toto.in_toto_verify import main as in_toto_verify_main
from in_toto.in_toto_verify import in_toto_verify
from in_toto import exceptions
from in_toto.util import import_rsa_key_from_file


class TestInTotoVerifyTool(unittest.TestCase):
  """
  Tests
    - in_toto_verify's main() - requires sys.argv patching;
    - in_toto_verify - calls verifylib.in_toto_verify and error logs/exits
      in case of a raised Exception.

  Uses in-toto demo supply chain link metadata files and basic layout for
  verification:

  Copies the basic layout for different test scenarios:
    - signed layout
    - multiple signed layout (using two project owner keys)
  """

  @classmethod
  def setUpClass(self):
    """Creates and changes into temporary directory.
    Copies demo files to temp dir...
      - owner/functionary key pairs
      - *.link metadata files
      - layout template (not signed, no expiration date)
      - final product

    ...and dumps various layouts for different test scenarios
    """
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
    layout_template = Metablock.load("demo.layout.template")

    # Store layout paths to be used in tests
    self.layout_single_signed_path = "single-signed.layout"
    self.layout_double_signed_path = "double-signed.layout"

    # Import layout signing keys
    alice = import_rsa_key_from_file("alice")
    bob = import_rsa_key_from_file("bob")
    self.alice_path = "alice.pub"
    self.bob_path = "bob.pub"

    # dump a single signed layout
    layout_template.sign(alice)
    layout_template.dump(self.layout_single_signed_path)
    # dump a double signed layout
    layout_template.sign(bob)
    layout_template.dump(self.layout_double_signed_path)

  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp dir. """
    os.chdir(self.working_dir)
    shutil.rmtree(self.test_dir)

  def test_main_required_args(self):
    """Test in-toto-verify CLI tool with required arguments. """
    args = [ "in-toto-verify", "--layout", self.layout_single_signed_path,
        "--layout-keys", self.alice_path]

    with patch.object(sys, 'argv', args):
      in_toto_verify_main()

  def test_main_wrong_args(self):
    """Test in-toto-verify CLI tool with wrong arguments. """
    wrong_args_list = [
      ["in-toto-verify"],
      ["in-toto-verify", "--layout", self.layout_single_signed_path],
      ["in-toto-verify", "--key", self.alice_path]]

    for wrong_args in wrong_args_list:
      with patch.object(sys, 'argv', wrong_args), self.assertRaises(SystemExit):
        in_toto_verify_main()

  def test_main_multiple_keys(self):
    """Test in-toto-verify CLI tool with multiple keys. """
    args = [ "in-toto-verify", "--layout", self.layout_double_signed_path,
        "--layout-keys", self.alice_path, self.bob_path]
    with patch.object(sys, 'argv', args):
      in_toto_verify_main()

  def test_in_toto_verify_pass_all(self):
    """Test in-toto-verify function pass verification. """
    in_toto_verify(self.layout_single_signed_path, [self.alice_path], None, None)

  def test_in_toto_verify_fail(self):
    """Test in-toto-verify function fail verification. """
    with self.assertRaises(SystemExit):
      in_toto_verify("wrong-layout-path", [self.alice_path], None, None)


class TestInTotoVerifyToolGPG(unittest.TestCase):
  """ Tests in-toto-verify like TestInTotoVerifyTool but with
  gpg project owner and functionary keys. """

  @classmethod
  def setUpClass(self):
    """Copy test gpg rsa keyring, gpg demo metadata files and demo final
    product to tmp test dir. """

    self.working_dir = os.getcwd()
    self.test_dir = os.path.realpath(tempfile.mkdtemp())

    # Copy gpg keyring
    gpg_keyring_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "gpg_keyrings", "rsa")

    self.gnupg_home = os.path.join(self.test_dir, "rsa")
    shutil.copytree(gpg_keyring_path, self.gnupg_home)

    self.owner_gpg_keyid = "8465a1e2e0fb2b40adb2478e18fb3f537e0c8a17"

    # Copy gpg demo metadata files
    demo_files = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "demo_files_gpg")
    for file in os.listdir(demo_files):
      shutil.copy(os.path.join(demo_files, file), self.test_dir)

    # Change into test dir
    os.chdir(self.test_dir)

    # Sign layout template with gpg key
    layout_template = Metablock.load("demo.layout.template")

    self.layout_path = "gpg_signed.layout"
    layout_template.sign_gpg(self.owner_gpg_keyid, self.gnupg_home)
    layout_template.dump(self.layout_path)


  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp dir. """
    os.chdir(self.working_dir)
    shutil.rmtree(self.test_dir)

  def test_gpg_signed_layout_with_gpg_functionary_keys(self):
    """ Successfully test demo supply chain where the layout lists gpg keys
    as functionary keys and is signed with a gpg key. """
    args = [ "in-toto-verify", "--layout", self.layout_path,
            "--gpg", self.owner_gpg_keyid, "--gpg-home", self.gnupg_home]

    with patch.object(sys, 'argv', args):
      in_toto_verify_main()


if __name__ == "__main__":
  unittest.main()
