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
import datetime
from in_toto.models.layout import Layout, Step, Inspection
import in_toto.models.link
import in_toto.exceptions
import securesystemslib.exceptions

class TestLayoutValidator(unittest.TestCase):
  """Test verifylib.verify_delete_rule(rule, artifact_queue) """

  def setUp(self):
    """Populate a base layout that we can use."""
    self.layout = Layout()
    self.layout.signed.expires = '2016-11-18T16:44:55Z'

  def test_wrong_type(self):
    """Test that the type field is validated properly."""

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.signed._type = "wrong"
      self.layout.signed._validate_type()
      self.layout.signed.validate()

    self.layout.signed._type = "layout"
    self.layout.signed._validate_type()

  def test_validate_readme_field(self):
    """Tests the readme field data type validator. """
    self.layout.signed.readme = 1
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.signed._validate_readme()

    self.layout.signed.readme = "This is a test supply chain"
    self.layout.signed._validate_readme()

  def test_wrong_expires(self):
    """Test the expires field is properly populated."""

    self.layout.signed.expires = ''
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.signed._validate_expires()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.signed.validate()

    self.layout.signed.expires = '-1'
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.signed._validate_expires()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.signed.validate()

    # notice the wrong month
    self.layout.signed.expires = '2016-13-18T16:44:55Z'
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.signed._validate_expires()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.signed.validate()

    self.layout.signed.expires = '2016-11-18T16:44:55Z'
    self.layout.signed._validate_expires()
    self.layout.signed.validate()

  def test_wrong_key_dictionary(self):
    """Test that the keys dictionary is properly populated."""
    rsa_key_one = securesystemslib.keys.generate_rsa_key()
    rsa_key_two = securesystemslib.keys.generate_rsa_key()

    # FIXME: attr.ib reutilizes the default dictionary, so future constructor
    # are not empty...
    self.layout.signed.keys = {"kek": rsa_key_one}
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.signed._validate_keys()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.signed.validate()

    self.layout.signed.keys = {}
    self.layout.signed.keys[rsa_key_two['keyid']] = "kek"
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.signed._validate_keys()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.signed.validate()

    self.layout.signed.keys = {}
    del rsa_key_one["keyval"]["private"]
    del rsa_key_two["keyval"]["private"]
    self.layout.signed.keys[rsa_key_one['keyid']] = rsa_key_one
    self.layout.signed.keys[rsa_key_two['keyid']] = rsa_key_two

    self.layout.signed._validate_keys()
    self.layout.signed.validate()

  def test_wrong_steps_list(self):
    """Check that the validate method checks the steps' correctness."""
    self.layout.signed.steps = "not-a-step"

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.signed.validate()

    test_step = Step(name="this-is-a-step")
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      test_step.expected_materials = ['this is a malformed step']
      self.layout.signed.steps = [test_step]
      self.layout.signed.validate()

    test_step = Step(name="this-is-a-step")
    test_step.expected_materials = [["CREATE", "foo"]]
    test_step.threshold = 1
    self.layout.signed.steps = [test_step]
    self.layout.signed.validate()

  def test_wrong_inspect_list(self):
    """Check that the validate method checks the inspections' correctness."""

    self.layout.signed.inspect = "not-an-inspection"
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.signed.validate()

    test_inspection = Inspection(name="this-is-a-step")
    test_inspection.expected_materials = ['this is a malformed artifact rule']
    self.layout.signed.inspect = [test_inspection]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.signed.validate()

    test_inspection = Inspection(name="this-is-a-step")
    test_inspection.expected_materials = [["CREATE", "foo"]]
    self.layout.signed.inspect = [test_inspection]
    self.layout.signed.validate()

  def test_repeated_step_names(self):
    """Check that only unique names exist in the steps and inspect lists"""

    self.layout.signed.steps = [Step(name="name"), Step(name="name")]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.signed.validate()

    self.layout.signed.steps = [Step(name="name")]
    self.layout.signed.inspect = [Inspection(name="name")]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.layout.signed.validate()

    self.layout.signed.step = [Step(name="name"), Step(name="othername")]
    self.layout.signed.inspect = [Inspection(name="thirdname")]
    self.layout.signed.validate()

  def test_import_step_metadata_wrong_type(self):
    functionary_key = securesystemslib.keys.generate_rsa_key()
    name = "name"

    # Create and dump a link file with a wrong type
    link_name = in_toto.models.link.FILENAME_FORMAT.format(
        step_name=name, keyid=functionary_key["keyid"])
    link_path = os.path.abspath(link_name)
    link = in_toto.models.link.Link(name=name)
    link.signed._type = "wrong-type"
    link.dump(link_path)

    # Add the single step to the test layout and try to read the failing link
    self.layout.signed.steps.append(Step(
        name=name, pubkeys=[functionary_key["keyid"]]))

    with self.assertRaises(in_toto.exceptions.LinkNotFoundError):
      self.layout.import_step_metadata_from_files_as_dict()

    # Clean up
    os.remove(link_path)

  def test_step_expected_command_shlex(self):
    """Check that a step's `expected_command` passed as string is converted
    to a list (using `shlex`). """
    step = Step(**{"expected_command": "rm -rf /"})
    self.assertTrue(isinstance(step.expected_command, list))
    self.assertTrue(len(step.expected_command) == 3)

if __name__ == "__main__":
  unittest.main()
