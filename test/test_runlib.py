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
from in_toto import ssl_crypto
from in_toto.runlib import in_toto_record_start, in_toto_record_stop, \
    UNFINISHED_FILENAME_FORMAT, record_artifacts_as_dict, \
    _apply_exclude_patterns
from in_toto.util import generate_and_write_rsa_keypair, \
    prompt_import_rsa_key_from_file
from in_toto.models.link import Link
from in_toto.exceptions import SignatureVerificationError
from simple_settings import settings


WORKING_DIR = os.getcwd()

class Test_ApplyExcludePatterns(unittest.TestCase):
  """Test _apply_exclude_patterns(names, exclude_patterns) """

  def test_apply_exclude_explict(self):
    names = ["foo", "bar", "baz"]
    patterns = ["foo", "bar"]
    expected = ["baz"]
    result = _apply_exclude_patterns(names, patterns)
    self.assertListEqual(sorted(result), sorted(expected))

  def test_apply_exclude_all(self):
    names = ["foo", "bar", "baz"]
    patterns = ["*"]
    expected = []
    result = _apply_exclude_patterns(names, patterns)
    self.assertListEqual(sorted(result), sorted(expected))

  def test_apply_exclude_multiple_star(self):
    names = ["foo", "bar", "baz"]
    patterns = ["*a*"]
    expected = ["foo"]
    result = _apply_exclude_patterns(names, patterns)
    self.assertListEqual(sorted(result), sorted(expected))


class TestRecordArtifactsAsDict(unittest.TestCase):
  """Test record_artifacts_as_dict(artifacts). """

  @classmethod
  def setUpClass(self):
    """Create and change into temp test directory with dummy artifacts. """
    # Clear user set excludes
    settings.ARTIFACT_EXCLUDES = []

    self.test_dir = tempfile.mkdtemp()
    os.chdir(self.test_dir)
    open("foo", "w").write("foo")
    open("bar", "w").write("bar")

    os.mkdir("subdir")
    open("subdir/foosub", "w").write("subfoo")

  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp test directory. """
    os.chdir(WORKING_DIR)
    shutil.rmtree(self.test_dir)

  def test_empty_artifacts_list_record_nothing(self):
    """Empty list passed. Return empty dict. """
    self.assertDictEqual(record_artifacts_as_dict([]), {})

  def test_not_existing_artifacts_in_list_record_nothing(self):
    """List with not existing artifact passed. Return empty dict. """
    self.assertDictEqual(record_artifacts_as_dict(["baz"]), {})

  def test_record_dot_check_files_hash_dict_schema(self):
    """Traverse dir and subdir. Record three files. """
    artifacts_dict = record_artifacts_as_dict(["."])

    for key, val in artifacts_dict.iteritems():
      ssl_crypto.formats.HASHDICT_SCHEMA.check_match(val)

    self.assertListEqual(sorted(artifacts_dict.keys()),
      sorted(["foo", "bar", "subdir/foosub"]))

  def test_record_files_and_subdir(self):
    """Explicitly record files and subdir. """
    artifacts_dict = record_artifacts_as_dict(["foo", "subdir"])

    for key, val in artifacts_dict.iteritems():
      ssl_crypto.formats.HASHDICT_SCHEMA.check_match(val)

    self.assertListEqual(sorted(artifacts_dict.keys()),
      sorted(["foo", "subdir/foosub"]))

  def test_record_dot_exclude_foo_star_from_recording(self):
    """Traverse dir and subdir from. Exclude pattern. Record one file. """
    settings.ARTIFACT_EXCLUDES = ["foo*"]
    artifacts_dict = record_artifacts_as_dict(["."])

    ssl_crypto.formats.HASHDICT_SCHEMA.check_match(artifacts_dict["bar"])
    self.assertListEqual(artifacts_dict.keys(), ["bar"])
    settings.ARTIFACT_EXCLUDES = []


class TestInTotoRecordStart(unittest.TestCase):
  """"Test in_toto_record_start(step_name, key, material_list). """

  @classmethod
  def setUpClass(self):
    """Create and change into temporary directory, generate key pair and dummy
    material, read key pair. """
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
