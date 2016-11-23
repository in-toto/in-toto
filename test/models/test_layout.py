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

import unittest
import datetime
from toto.models.layout import Layout, Step, Inspection
from toto.ssl_commons.exceptions import FormatError
import toto.ssl_crypto

class TestLayoutValidator(unittest.TestCase):
  """Test verifylib.verify_delete_rule(rule, artifact_queue) """

  def setUp(self):
    """Populate a base layout that we can use."""
    self.layout = Layout()
    self.layout.expires = '2016-11-18T16:44:55Z'

  def test_wrong_type(self):
    """Test that the type field is validated properly."""

    with self.assertRaises(FormatError):
      self.layout._type = "wrong"
      self.layout._validate_type()
      self.layout.validate()

    self.layout._type = "layout"
    self.layout._validate_type()

  def test_wrong_expires(self):
    """Test the expires field is properly populated."""

    self.layout.expires = ''
    with self.assertRaises(FormatError):
      self.layout._validate_expires()

    with self.assertRaises(FormatError):
      self.layout.validate()

    self.layout.expires = '-1'
    with self.assertRaises(FormatError):
      self.layout._validate_expires()

    with self.assertRaises(FormatError):
      self.layout.validate()

    # notice the wrong month
    self.layout.expires = '2016-13-18T16:44:55Z'
    with self.assertRaises(FormatError):
      self.layout._validate_expires()

    with self.assertRaises(FormatError):
      self.layout.validate()

    self.layout.expires = '2016-11-18T16:44:55Z'
    self.layout._validate_expires()
    self.layout.validate()

  def test_wrong_key_dictionary(self):
    """Test that the keys dictionary is properly populated."""
    rsa_key_one = toto.ssl_crypto.keys.generate_rsa_key()
    rsa_key_two = toto.ssl_crypto.keys.generate_rsa_key()

    # FIXME: attr.ib reutilizes the default dictionary, so future constructor
    # are not empty...
    self.layout.keys = {"kek": rsa_key_one}
    with self.assertRaises(FormatError):
      self.layout._validate_keys()

    with self.assertRaises(FormatError):
      self.layout.validate()

    self.layout.keys = {}
    self.layout.keys[rsa_key_two['keyid']] = "kek"
    with self.assertRaises(FormatError):
      self.layout._validate_keys()

    with self.assertRaises(FormatError):
      self.layout.validate()

    self.layout.keys = {}
    self.layout.keys[rsa_key_one['keyid']] = rsa_key_one
    self.layout.keys[rsa_key_two['keyid']] = rsa_key_two

    self.layout._validate_keys()
    self.layout.validate()

  def test_wrong_steps_list(self):
    """Check that the validate method checks the steps' correctness."""
    self.layout.steps = "not-a-step"

    with self.assertRaises(FormatError):
      self.layout.validate()

    test_step = Step("this-is-a-step")
    with self.assertRaises(FormatError):
      test_step.material_matchrules = ['this is a malformed step']
      self.layout.steps = [test_step]
      self.layout.validate()


    test_step = Step("this-is-a-step")
    test_step.material_matchrules = [["CREATE", "foo"]]
    test_step.threshold = 1
    self.layout.steps = [test_step]
    self.layout.validate()

  def test_wrong_inspect_list(self):
    """Check that the validate method checks the inspections' correctness."""

    self.layout.inspect = "not-an-inspection"
    with self.assertRaises(FormatError):
      self.layout.validate()

    test_inspection = Inspection("this-is-a-step")
    test_inspection.material_matchrules = ['this is a malformed matchrule']
    self.layout.inspect = [test_inspection]
    with self.assertRaises(FormatError):
      self.layout.validate()

    test_inspection = Inspection("this-is-a-step")
    test_inspection.material_matchrules = [["CREATE", "foo"]]
    self.layout.inspect = [test_inspection]
    self.layout.validate()

  def test_repeated_step_names(self):
    """Check that only unique names exist in the steps and inspect lists"""

    self.layout.steps = [Step("name"), Step("name")]
    with self.assertRaises(FormatError):
      self.layout.validate()

    self.layout.steps = [Step("name")]
    self.layout.inspect = [Inspection("name")]
    with self.assertRaises(FormatError):
      self.layout.validate()

    self.layout.step = [Step("name"), Step("othername")]
    self.layout.inspect = [Inspection("thirdname")]
    self.layout.validate()

if __name__ == '__main__':

  unittest.main()
