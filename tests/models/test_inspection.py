#!/usr/bin/env python
"""
<Program Name>
  test_inspection.py

<Author>
  Santiago Torres-Arias <santiago@nyu.edu>

<Started>
  Nov 18, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test inspection class functions.

"""

import unittest
from in_toto.models.layout import Layout, Inspection
import securesystemslib.exceptions

class TestInspectionValidator(unittest.TestCase):
  """Test verifylib.verify_delete_rule(rule, artifact_queue) """

  def setUp(self):
    """Populate a base layout that we can use."""
    self.inspection = Inspection(name="some-inspection")

  def test_wrong_type(self):
    """Test the type field within Validate()."""

    self.inspection._type = "wrong"
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.inspection._validate_type()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.inspection.validate()

    self.inspection._type = "inspection"
    self.inspection._validate_type()

  def test_wrong_expected_materials(self):
    """Test that the material rule validators catch malformed ones."""

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.inspection.expected_materials = [["NONFOO"]]
      self.inspection._validate_expected_materials()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.inspection.validate()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.inspection.expected_materials = "PFF"
      self.inspection._validate_expected_materials()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.inspection.validate()

    # for more thorough tests, check the test_rulelib.py module
    self.inspection.expected_materials = [["CREATE", "foo"]]
    self.inspection._validate_expected_materials()
    self.inspection.validate()

  def test_wrong_expected_products(self):
    """Test that the product rule validators catch malformed values."""

    self.inspection.expected_products = [["NONFOO"]]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.inspection._validate_expected_products()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.inspection.validate()

    self.inspection.expected_products = "PFF"
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.inspection._validate_expected_products()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.inspection.validate()

    # for more thorough tests, check the test_rulelib.py module
    self.inspection.expected_products = [["CREATE", "foo"]]
    self.inspection._validate_expected_products()
    self.inspection.validate()

  def test_wrong_run(self):
    """Test that the run validators catch malformed values."""

    self.inspection.run = -1
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.inspection._validate_run()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.inspection.validate()

    self.inspection.run = ["somecommand"]
    self.inspection._validate_run()
    self.inspection.validate()

if __name__ == '__main__':

  unittest.main()
