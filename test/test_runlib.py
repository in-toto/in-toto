#!/usr/bin/env python

"""
<Program Name>
  test_runlib.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Dec 01, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test runlib functions.

"""

import os
import unittest
import shutil
import tempfile
from toto.runlib import in_toto_record_start, in_toto_record_stop, \
    UNFINISHED_FILENAME_FORMAT
from toto.util import generate_and_write_rsa_keypair, \
    prompt_import_rsa_key_from_file
from toto.models.link import Link
from toto.exceptions import SignatureVerificationError


WORKING_DIR = os.getcwd()


class TestInTotoRecordStart(unittest.TestCase):
  """"Test in_toto_record_start(step_name, key, material_list). """

  @classmethod
  def setUpClass(self):
    """Create and change into temporary directory, generate key pair and dummy
    material, read key pai. """
    self.test_dir = tempfile.mkdtemp()
    os.chdir(self.test_dir)

    self.step_name = "test_step"
    self.link_name_unfinished = UNFINISHED_FILENAME_FORMAT.format(
        step_name=self.step_name)

    self.key_path = "test_key"
    generate_and_write_rsa_keypair(self.key_path)
    self.key = prompt_import_rsa_key_from_file(self.key_path)

    self.test_material= "test_material"
    open(self.test_material, "w").close()

  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp test directory. """
    os.chdir(WORKING_DIR)
    shutil.rmtree(self.test_dir)

  def test_unfinished_filename_format(self):
    """Test if the unfinished filname format. """
    self.assertTrue(self.link_name_unfinished ==
        ".{}.link-unfinished".format(self.step_name))

  def test_create_unfinished_metadata_with_expected_material(self):
    """Test record start creates metadata with expected material. """
    in_toto_record_start(
        self.step_name, self.key, [self.test_material])
    link = Link.read_from_file(self.link_name_unfinished)
    self.assertEquals(link.materials.keys(), [self.test_material])
    os.remove(self.link_name_unfinished)

  def test_create_unfininished_metadata_verify_signature(self):
    """Test record start creates metadata with expected signature. """
    in_toto_record_start(
        self.step_name, self.key, [self.test_material])
    link = Link.read_from_file(self.link_name_unfinished)
    link.verify_signatures({self.key["keyid"] : self.key})
    os.remove(self.link_name_unfinished)


class TestInTotoRecordStop(unittest.TestCase):
  """"Test in_toto_record_stop(step_name, key, product_list). """

  @classmethod
  def setUpClass(self):
    """Create and change into temporary directory, generate two key pairs
    and dummy product. """
    self.test_dir = tempfile.mkdtemp()
    os.chdir(self.test_dir)

    self.step_name = "test-step"
    self.link_name = "{}.link".format(self.step_name)
    self.link_name_unfinished = UNFINISHED_FILENAME_FORMAT.format(
        step_name=self.step_name)

    self.key_path = "test-key"
    self.key_path2 = "test-key2"
    generate_and_write_rsa_keypair(self.key_path)
    generate_and_write_rsa_keypair(self.key_path2)
    self.key = prompt_import_rsa_key_from_file(self.key_path)
    self.key2 = prompt_import_rsa_key_from_file(self.key_path2)

    self.test_product = "test_product"
    open(self.test_product, "w").close()

  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp test directory. """
    os.chdir(WORKING_DIR)
    shutil.rmtree(self.test_dir)

  def test_create_metadata_with_expected_product(self):
    """Test record stop records expected product. """
    in_toto_record_start(self.step_name, self.key, [])
    in_toto_record_stop(
        self.step_name, self.key, [self.test_product])
    link = Link.read_from_file(self.link_name)
    self.assertEquals(link.products.keys(), [self.test_product])
    os.remove(self.link_name)

  def test_create_metadata_verify_signature(self):
    """Test record start creates metadata with expected signature. """
    in_toto_record_start(self.step_name, self.key, [])
    in_toto_record_stop(
        self.step_name, self.key, [])
    link = Link.read_from_file(self.link_name)
    link.verify_signatures({self.key["keyid"] : self.key})
    os.remove(self.link_name)

  def test_replace_unfinished_metadata(self):
    """Test record stop removes unfinished file and creates link file. """
    in_toto_record_start(self.step_name, self.key, [])
    in_toto_record_stop(self.step_name, self.key, [])
    with self.assertRaises(IOError):
      open(self.link_name_unfinished, "r")
    open(self.link_name, "r")
    os.remove(self.link_name)

  def test_missing_unfinished_file(self):
    """Test record stop exits on missing unfinished file, no link recorded. """
    with self.assertRaises(IOError):
      in_toto_record_stop(self.step_name, self.key, [])
    with self.assertRaises(IOError):
      open(self.link_name, "r")

  def test_wrong_signature_in_unfinished_metadata(self):
    """Test record stop exits on wrong signature, no link recorded. """
    in_toto_record_start(self.step_name, self.key, [])
    with self.assertRaises(SignatureVerificationError):
      in_toto_record_stop(self.step_name, self.key2, [])
    with self.assertRaises(IOError):
      open(self.link_name, "r")
    os.remove(self.link_name_unfinished)

if __name__ == '__main__':
  unittest.main()
