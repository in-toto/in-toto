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
from toto.models.layout import Layout, Inspection
from toto.ssl_commons.exceptions import FormatError
import toto.ssl_crypto

class TestInspectionValidator(unittest.TestCase):
  """Test verifylib.verify_delete_rule(rule, artifact_queue) """

  def setUp(self):
    """Populate a base layout that we can use."""
    self.inspection = Inspection("some-inspection")

  def test_wrong_type(self):
    """Test the type field within Validate()."""

    self.inspection._type = "wrong"
    with self.assertRaises(FormatError):
      self.inspection._validate_type()

    with self.assertRaises(FormatError):
      self.inspection.validate()

    self.inspection._type = "inspection"
    self.inspection._validate_type()

  def test_wrong_material_matchrules(self):
    """Test that the material matchrule validators catch malformed ones."""

    with self.assertRaises(FormatError):
      self.inspection.material_matchrules = [["NONFOO"]]
      self.inspection._validate_material_matchrules()

    with self.assertRaises(FormatError):
      self.inspection.validate()

    with self.assertRaises(FormatError):
      self.inspection.material_matchrules = "PFF"
      self.inspection._validate_material_matchrules()

    with self.assertRaises(FormatError):
      self.inspection.validate()

    # for more thorough tests, check the test_matchrule.py module
    self.inspection.material_matchrules = [["CREATE", "foo"]]
    self.inspection._validate_material_matchrules()
    self.inspection.validate()

  def test_wrong_product_matchrules(self):
    """Test that the product matchrule validators catch malformed values."""

    self.inspection.product_matchrules = [["NONFOO"]]
    with self.assertRaises(FormatError):
      self.inspection._validate_product_matchrules()

    with self.assertRaises(FormatError):
      self.inspection.validate()

    self.inspection.product_matchrules = "PFF"
    with self.assertRaises(FormatError):
      self.inspection._validate_product_matchrules()

    with self.assertRaises(FormatError):
      self.inspection.validate()

    # for more thorough tests, check the test_matchrule.py module
    self.inspection.product_matchrules = [["CREATE", "foo"]]
    self.inspection._validate_product_matchrules()
    self.inspection.validate()

  def test_wrong_run(self):
    """Test that the run validators catch malformed values."""

    self.inspection.run = -1
    with self.assertRaises(FormatError):
      self.inspection._validate_run()

    with self.assertRaises(FormatError):
      self.inspection.validate()

    self.inspection.run = "somecommand"
    self.inspection._validate_run()
    self.inspection.validate()

if __name__ == '__main__':

  unittest.main()
