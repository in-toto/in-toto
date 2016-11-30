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

from toto.util import generate_and_write_rsa_keypair
from toto.models.link import Link
from toto.in_toto_record import main as in_toto_record_main
from toto.in_toto_record import in_toto_record_start, in_toto_record_stop

WORKING_DIR = os.getcwd()

# Suppress all the user feedback that we print using a base logger
logging.getLogger().setLevel(logging.CRITICAL)

class TestInTotoRecordMain(unittest.TestCase):
  """Test in_toto_record's main() - requires sys.argv patching. """

  @classmethod
  def setUpClass(self):
    """Create and change into temporary directory,
    generate key pair, dummy artifact and base arguments. """
    self.test_dir = tempfile.mkdtemp()
    os.chdir(self.test_dir)

    self.test_key = "test_key"
    generate_and_write_rsa_keypair(self.test_key)

    self.test_artifact = "test_artifact"
    open(self.test_artifact, "w").close()

    self.args = [
        "in_toto_record.py",
        "--step-name",
        "test-step",
        "--key",
        self.test_key
    ]

  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp test directory. """
    os.chdir(WORKING_DIR)
    shutil.rmtree(self.test_dir)

  def test_command_start_stop_required_args(self):
    """Test CLI command record start/stop with required arguments. """
    with patch.object(sys, 'argv',  self.args + ["start"]):
      in_toto_record_main()

    with patch.object(sys, 'argv', self.args + ["stop"]):
      in_toto_record_main()

  def test_command_start_stop_optional_args(self):
    """Test CLI command record start/stop with optional arguments. """
    with patch.object(sys, 'argv', self.args + ["start", "--materials",
        self.test_artifact]):
      in_toto_record_main()

    with patch.object(sys, 'argv', self.args + ["stop", "--products",
        self.test_artifact]):
      in_toto_record_main()


class TestInTotoRecordStart(unittest.TestCase):
  """"Test in_toto_record_start(step_name, key_path, material_list). """

  @classmethod
  def setUpClass(self):
    """Create and change into temporary directory, generate key pair and dummy
    material. """
    self.test_dir = tempfile.mkdtemp()
    os.chdir(self.test_dir)

    self.step_name = "test-step"
    self.link_name_unfinished = ".{}.link-unfinished".format(self.step_name)

    self.key_path = "test_key"
    generate_and_write_rsa_keypair(self.key_path)

    self.test_material= "test_material"
    open(self.test_material, "w").close()

  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp test directory. """
    os.chdir(WORKING_DIR)
    shutil.rmtree(self.test_dir)

  def test_create_link_unfinished_file(self):
    """Test record start creates a link metadata file. """
    in_toto_record_start(self.step_name, self.key_path, [self.test_material])
    open(self.link_name_unfinished)

  def test_record_test_material(self):
    """Test record start records expected material. """
    in_toto_record_start(
        self.step_name, self.key_path, [self.test_material])
    link = Link.read_from_file(self.link_name_unfinished)
    self.assertEquals(link.materials.keys(), [self.test_material])


class TestInTotoRecordStop(unittest.TestCase):
  """"Test in_toto_record_stop(step_name, key_path, product_list). """

  @classmethod
  def setUpClass(self):
    """Create and change into temporary directory, generate two key pairs
    and dummy product. """
    self.test_dir = tempfile.mkdtemp()
    os.chdir(self.test_dir)

    self.step_name = "test-step"
    self.link_name = "{}.link".format(self.step_name)
    self.link_name_unfinished = ".{}.link-unfinished".format(self.step_name)

    self.key_path = "test-key"
    self.key_path2 = "test-key2"
    generate_and_write_rsa_keypair(self.key_path)
    generate_and_write_rsa_keypair(self.key_path2)

    self.test_product = "test_product"
    open(self.test_product, "w").close()

  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp test directory. """
    os.chdir(WORKING_DIR)
    shutil.rmtree(self.test_dir)

  def test_record_test_product(self):
    """Test record stop records expected product. """
    in_toto_record_start(self.step_name, self.key_path, [])
    in_toto_record_stop(
        self.step_name, self.key_path, [self.test_product])
    link = Link.read_from_file(self.link_name)
    self.assertEquals(link.products.keys(), [self.test_product])

  def test_replace_unfinished_file(self):
    """Test record stop removes unfinished file. """
    in_toto_record_start(self.step_name, self.key_path, [])
    in_toto_record_stop(self.step_name, self.key_path, [])
    with self.assertRaises(IOError):
      open(self.link_name_unfinished, "r")
    open(self.link_name, "r")

  def test_missing_unfinished_file(self):
    """Test record stop exits on missing unfinished file. """
    with self.assertRaises(SystemExit):
      in_toto_record_stop(self.step_name, self.key_path, [])

  def test_wrong_signature_in_unfinished_file(self):
    """Test record stop exits on wrong signature. """
    in_toto_record_start(self.step_name, self.key_path, [])
    with self.assertRaises(SystemExit):
      in_toto_record_stop(self.step_name, self.key_path2, [])



if __name__ == '__main__':
  unittest.main()
