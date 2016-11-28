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
  Test step class functions.

"""

import unittest
import datetime
from toto.models.layout import Step
from toto.ssl_commons.exceptions import FormatError
import toto.ssl_crypto

class TestStepValidator(unittest.TestCase):
  """Test verifylib.verify_delete_rule(rule, artifact_queue) """

  def setUp(self):
    """Populate a base layout that we can use."""
    self.step = Step("this-step")

  def test_wrong_type(self):
    """Test the type field within Validate()."""

    self.step._type = "wrong"
    with self.assertRaises(FormatError):
      self.step._validate_type()

    with self.assertRaises(FormatError):
      self.step.validate()

    self.step._type = "step"
    self.step._validate_type()

  @unittest.skip("Model requires changes")
  def test_wrong_threshold(self):
    """Test that the threshold value is correctly checked."""

    # no, python is not *this* smart
    self.step.threshold = "Ten"
    with self.assertRaises(FormatError):
      self.step._validate_threshold()

    with self.assertRaises(FormatError):
      self.step.validate()

    self.step.threshold = 10
    self.step._validate_threshold()
    self.step.validate()

  def test_wrong_material_matchrules(self):
    """Test that the material matchrule validators catch malformed ones."""

    self.step.material_matchrules = [["NONFOO"]]
    with self.assertRaises(FormatError):
      self.step._validate_material_matchrules()

    with self.assertRaises(FormatError):
      self.step.validate()

    self.step.material_matchrules = "PFF"
    with self.assertRaises(FormatError):
      self.step._validate_material_matchrules()

    with self.assertRaises(FormatError):
      self.step.validate()

    # for more thorough tests, check the test_matchrule.py module
    self.step.material_matchrules = [["CREATE", "foo"]]
    self.step._validate_material_matchrules()
    self.step.validate()

  def test_wrong_product_matchrules(self):
    """Test that the product matchrule validators catch malformed ones."""

    self.step.product_matchrules = [["NONFOO"]]
    with self.assertRaises(FormatError):
      self.step._validate_product_matchrules()

    with self.assertRaises(FormatError):
      self.step.validate()

    self.step.product_matchrules = "PFF"
    with self.assertRaises(FormatError):
      self.step._validate_product_matchrules()

    with self.assertRaises(FormatError):
      self.step.validate()

    # for more thorough tests, check the test_matchrule.py module
    self.step.product_matchrules = [["CREATE", "foo"]]
    self.step._validate_product_matchrules()
    self.step.validate()

  def test_wrong_pubkeys(self):
    # FIXME: generating keys for each test are expensive processes, maybe we
    # should have an asset/fixture folder/loader?

    rsa_key_one = toto.ssl_crypto.keys.generate_rsa_key()
    rsa_key_two = toto.ssl_crypto.keys.generate_rsa_key()

    self.step.pubkeys = ['bad-keyid']

    with self.assertRaises(FormatError):
      self.step._validate_pubkeys()

    with self.assertRaises(FormatError):
      self.step.validate()

    self.step.pubkeys = [rsa_key_one['keyid'], rsa_key_two['keyid']]
    self.step._validate_pubkeys()
    self.step.validate()

  def test_wrong_expected_command(self):
    """Test that the expected command validator catches malformed ones."""

    self.step.expected_command = -1
    with self.assertRaises(FormatError):
      self.step._validate_expected_command()

    with self.assertRaises(FormatError):
      self.step.validate()

    self.step.expected_command = "somecommand"
    self.step._validate_expected_command()
    self.step.validate()

if __name__ == '__main__':

  unittest.main()
