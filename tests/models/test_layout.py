#!/usr/bin/env python
"""
<Program Name>
  test_layout.py

<Author>
  Santiago Torres-Arias <santiago@nyu.edu>

<Started>
  Nov 18, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test layout class functions.

"""

import os
import unittest
import shutil

from in_toto.models.layout import Layout, Step, Inspection
from in_toto.models.metadata import Metablock
import in_toto.models.link
import in_toto.exceptions
import in_toto.verifylib
import securesystemslib.exceptions

from tests.common import TmpDirMixin, GPGKeysMixin

class TestLayoutMethods(unittest.TestCase, TmpDirMixin, GPGKeysMixin):
  """Test Layout methods. """

  @classmethod
  def setUpClass(self):
    """Create temporary test directory and copy gpg keychain, and rsa keys from
    demo files. """
    demo_files = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "..", "demo_files")

    self.set_up_test_dir()
    self.set_up_gpg_keys()


    # Copy keys to temp test dir
    key_names = ["bob", "bob.pub", "carl.pub"]
    for name in key_names:
      shutil.copy(os.path.join(demo_files, name), name)

    self.key_path = os.path.join(self.test_dir, "bob")
    self.pubkey_path1 = os.path.join(self.test_dir, "bob.pub")
    self.pubkey_path2 = os.path.join(self.test_dir, "carl.pub")


  @classmethod
  def tearDownClass(self):
    self.tear_down_test_dir()


  def test_set_relative_expiration(self):
    """Test adding expiration date relative from today. """
    layout = Layout()
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      layout.set_relative_expiration(days=None, months=0, years=0)

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      layout.set_relative_expiration(days=0, months="", years=0)

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      layout.set_relative_expiration(days=0, months=0, years=[])

    layout.set_relative_expiration(days=1)
    layout._validate_expires()
    layout.set_relative_expiration(months=2)
    layout._validate_expires()
    layout.set_relative_expiration(years=3)
    layout._validate_expires()
    layout.set_relative_expiration(days=3, months=2, years=1)
    layout._validate_expires()

    # It's possible to add an expiration date in the past
    layout.set_relative_expiration(days=-3, months=-2, years=-1)
    layout._validate_expires()


  def test_get_step_name_list(self):
    """Test getting list of step names. """
    names = ["a", "b", "c"]
    layout = Layout(steps=[Step(name=name) for name in names])
    self.assertListEqual(layout.get_step_name_list(), names)


  def test_get_step_by_name(self):
    """Test getting step by name. """
    names = ["a", "b", "c"]
    layout = Layout(steps=[Step(name=name) for name in names])
    self.assertEqual(layout.get_step_by_name("b").name, "b")

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      layout.get_step_by_name(None)


  def test_remove_step_by_name(self):
    """Test removing step by name. """
    names = ["a", "b", "c"]
    layout = Layout(steps=[Step(name=name) for name in names])

    self.assertEqual(len(layout.steps), 3)
    self.assertTrue("b" in layout.get_step_name_list())
    # Items are only removed if they exist
    for _ in range(2):
      layout.remove_step_by_name("b")
      self.assertEqual(len(layout.steps), 2)
      self.assertTrue("b" not in layout.get_step_name_list())

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      layout.get_step_by_name([])


  def test_get_inspection_name_list(self):
    """Test getting list of inspection names. """
    names = ["a", "b", "c"]
    layout = Layout(inspect=[Inspection(name=name) for name in names])
    self.assertListEqual(layout.get_inspection_name_list(), names)


  def test_get_inspection_by_name(self):
    """Test getting inspection by name. """
    names = ["a", "b", "c"]
    layout = Layout(inspect=[Inspection(name=name) for name in names])
    self.assertEqual(layout.get_inspection_by_name("b").name, "b")

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      layout.get_inspection_by_name(1)


  def test_remove_inspection_by_name(self):
    """Test removing inspection by name. """
    names = ["a", "b", "c"]
    layout = Layout(inspect=[Inspection(name=name) for name in names])

    self.assertEqual(len(layout.inspect), 3)
    self.assertTrue("b" in layout.get_inspection_name_list())
    # Items are only removed if they exist
    for _ in range(2):
      layout.remove_inspection_by_name("b")
      self.assertEqual(len(layout.inspect), 2)
      self.assertTrue("b" not in layout.get_inspection_name_list())


    with self.assertRaises(securesystemslib.exceptions.FormatError):
      layout.remove_inspection_by_name(False)


  def test_functionary_keys(self):
    """Test adding and listing functionary keys (securesystemslib and gpg). """
    layout = Layout()
    self.assertEqual(len(layout.get_functionary_key_id_list()), 0)

    layout.add_functionary_keys_from_paths([self.pubkey_path1,
        self.pubkey_path2])

    layout.add_functionary_keys_from_gpg_keyids([self.gpg_key_768C43,
        self.gpg_key_85DA58], gpg_home=self.gnupg_home)

    layout._validate_keys()

    self.assertEqual(len(layout.get_functionary_key_id_list()), 4)

    # Must be a valid key object
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      layout.add_functionary_key("abcd")

    # Must be pubkey and not private key
    with self.assertRaises(securesystemslib.exceptions.Error):
      layout.add_functionary_key_from_path(self.key_path)

    # Must be a valid path
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      layout.add_functionary_key_from_path(123)

    # Must be a valid keyid
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      layout.add_functionary_key_from_gpg_keyid("abcdefg")

    # Must be a list of paths
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      layout.add_functionary_keys_from_paths("abcd")
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      layout.add_functionary_keys_from_paths([1])

    # Must be a list of keyids
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      layout.add_functionary_keys_from_gpg_keyids(None)
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      layout.add_functionary_keys_from_gpg_keyids(["abcdefg"])



class TestLayoutValidator(unittest.TestCase):
  """Test in_toto.models.layout.Layout validators. """


  def setUp(self):
    """Populate a base layout that we can use."""
    self.layout = Layout()
    self.layout.expires = '2016-11-18T16:44:55Z'


  def test_wrong_type(self):
    """Test that the type field is validated properly."""
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout._type = "wrong"
      self.layout._validate_type()
      self.layout.validate()

    self.layout._type = "layout"
    self.layout._validate_type()


  def test_validate_readme_field(self):
    """Tests the readme field data type validator. """
    self.layout.readme = 1
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout._validate_readme()

    self.layout.readme = "This is a test supply chain"
    self.layout._validate_readme()


  def test_wrong_expires(self):
    """Test the expires field is properly populated."""

    self.layout.expires = ''
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout._validate_expires()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.validate()

    self.layout.expires = '-1'
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout._validate_expires()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.validate()

    # notice the wrong month
    self.layout.expires = '2016-13-18T16:44:55Z'
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout._validate_expires()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.validate()

    self.layout.expires = '2016-11-18T16:44:55Z'
    self.layout._validate_expires()
    self.layout.validate()


  def test_wrong_key_dictionary(self):
    """Test that the keys dictionary is properly populated."""
    rsa_key_one = securesystemslib.keys.generate_rsa_key()
    rsa_key_two = securesystemslib.keys.generate_rsa_key()

    # FIXME: attr.ib reutilizes the default dictionary, so future constructor
    # are not empty...
    self.layout.keys = {"kek": rsa_key_one}
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout._validate_keys()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.validate()

    self.layout.keys = {}
    self.layout.keys[rsa_key_two['keyid']] = "kek"
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout._validate_keys()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.validate()

    self.layout.keys = {}
    del rsa_key_one["keyval"]["private"]
    del rsa_key_two["keyval"]["private"]
    self.layout.keys[rsa_key_one['keyid']] = rsa_key_one
    self.layout.keys[rsa_key_two['keyid']] = rsa_key_two

    self.layout._validate_keys()
    self.layout.validate()


  def test_wrong_steps_list(self):
    """Check that the validate method checks the steps' correctness."""
    self.layout.steps = "not-a-step"
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.validate()

    self.layout.steps = ["not-a-step"]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.validate()

    test_step = Step(name="this-is-a-step")
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      test_step.expected_materials = ['this is a malformed step']
      self.layout.steps = [test_step]
      self.layout.validate()

    test_step = Step(name="this-is-a-step")
    test_step.expected_materials = [["CREATE", "foo"]]
    test_step.threshold = 1
    self.layout.steps = [test_step]
    self.layout.validate()


  def test_wrong_inspect_list(self):
    """Check that the validate method checks the inspections' correctness."""

    self.layout.inspect = "not-an-inspection"
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.validate()

    self.layout.inspect = ["not-an-inspection"]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.validate()

    test_inspection = Inspection(name="this-is-a-step")
    test_inspection.expected_materials = ['this is a malformed artifact rule']
    self.layout.inspect = [test_inspection]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.validate()

    test_inspection = Inspection(name="this-is-a-step")
    test_inspection.expected_materials = [["CREATE", "foo"]]
    self.layout.inspect = [test_inspection]
    self.layout.validate()


  def test_repeated_step_names(self):
    """Check that only unique names exist in the steps and inspect lists"""

    self.layout.steps = [Step(name="name"), Step(name="name")]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.validate()

    self.layout.steps = [Step(name="name")]
    self.layout.inspect = [Inspection(name="name")]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.validate()

    self.layout.step = [Step(name="name"), Step(name="othername")]
    self.layout.inspect = [Inspection(name="thirdname")]
    self.layout.validate()


  def test_import_step_metadata_wrong_type(self):
    functionary_key = securesystemslib.keys.generate_rsa_key()
    name = "name"

    # Create and dump a link file with a wrong type
    link_name = in_toto.models.link.FILENAME_FORMAT.format(
        step_name=name, keyid=functionary_key["keyid"])

    link_path = os.path.abspath(link_name)
    link = in_toto.models.link.Link(name=name)
    metadata = Metablock(signed=link)
    metadata.signed._type = "wrong-type"
    metadata.dump(link_path)

    # Add the single step to the test layout and try to read the failing link
    self.layout.steps.append(Step(
        name=name, pubkeys=[functionary_key["keyid"]]))

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      in_toto.verifylib.load_links_for_layout(self.layout, ".")

    # Clean up
    os.remove(link_path)


  def test_wrong_pubkeys(self):
    """Check validate pubkeys fails with wrong keys."""
    # Pubkeys must be lists ...
    tmp_step = Step()
    tmp_step.pubkeys = "abcd"
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      tmp_step.validate()

    # ... of keyids (hex schema)
    tmp_step.pubkeys = ["abcdefg"]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      tmp_step.validate()

if __name__ == "__main__":
  unittest.main()
