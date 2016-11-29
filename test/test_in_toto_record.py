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
from mock import patch

from toto.util import generate_and_write_rsa_keypair
from toto.models.link import Link
from toto.in_toto_record import main as in_toto_record_main
from toto.in_toto_record import in_toto_record_start, in_toto_record_stop

# Suppress all the user feedback that we print using a base logger
logging.getLogger().setLevel(logging.CRITICAL)

def _try_remove_files(file_list):
  if not isinstance(file_list, list):
    return
  else:
    for path in file_list:
      try:
        os.remove(path)
      except Exception, e:
        pass


class TestInTotoRecordMain(unittest.TestCase):
  """Test in_toto_record's main() - requires sys.argv patching. """

  @classmethod
  def setUpClass(self):
    """Generate key pair, dummy artifact and base arguments. """
    generate_and_write_rsa_keypair("test-key")
    self.args = [
        "in_toto_record.py",
        "--step-name",
        "test-step",
        "--key",
        "test-key"
    ]
    self.test_artifact = "test-artifact"
    open(self.test_artifact, "a").close()

  @classmethod
  def tearDownClass(self):
    """Remove key pair, dummy artifact and link metadata. """
    files_to_remove = [
      "test-key", "test-key.pub", "test-step.link", self.test_artifact
    ]
    _try_remove_files(files_to_remove)


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
    """Generate key pair, dummy artifact and base arguments. """
    self.step_name = "test-step"
    self.key_path = "test-key"
    generate_and_write_rsa_keypair(self.key_path)
    self.test_material= "test-material"
    open(self.test_material, "a").close()

  @classmethod
  def tearDownClass(self):
    """Remove key pair, dummy artifact and link metadata. """
    files_to_remove = [
        self.key_path, self.key_path + ".pub", self.test_material,
        "." + self.step_name + ".link-unfinished"
      ]
    _try_remove_files(files_to_remove)

  def test_create_link_unfinished_file(self):
    """Test record start creates a link metadata file. """
    in_toto_record_start(self.step_name, self.key_path, [self.test_material])
    open("." + self.step_name + ".link-unfinished", "r")

  def test_record_test_material(self):
    """Test record start records expected material. """
    link = in_toto_record_start(
        self.step_name, self.key_path, [self.test_material])
    self.assertEquals(link.materials.keys(), [self.test_material])





class TestInTotoRecordStop(unittest.TestCase):
  """"Test in_toto_record_start(step_name, key_path, material_list). """

  @classmethod
  def setUpClass(self):
    """Generate key pair, dummy artifact and base arguments. """
    self.step_name = "test-step"
    self.key_path = "test-key"
    self.key_path2 = "test-key2"
    generate_and_write_rsa_keypair(self.key_path)
    generate_and_write_rsa_keypair(self.key_path)

    self.test_product = "test-product"
    open(self.test_product, "a").close()

  @classmethod
  def tearDownClass(self):
    """Remove key pair, dummy artifact and link metadata. """
    files_to_remove = [
      self.key_path, self.key_path + ".pub", self.key_path2,
      self.key_path2 + ".pub", self.test_product, self.step_name + ".link",
      "." + self.step_name + ".link-unfinished"
    ]
    _try_remove_files(files_to_remove)

  def test_record_test_product(self):
    """Test record stop records expected product. """
    in_toto_record_start(self.step_name, self.key_path, [])
    link = in_toto_record_stop(
        self.step_name, self.key_path, [self.test_product])
    self.assertEquals(link.products.keys(), [self.test_product])

  def test_replace_unfinished_file(self):
    """Test record stop removes unfinished file. """
    in_toto_record_start(self.step_name, self.key_path, [])
    in_toto_record_stop(self.step_name, self.key_path, [])
    with self.assertRaises(IOError):
      open("." + self.step_name + ".link-unfinished", "r")
    open(self.step_name + ".link", "r")

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
