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
    """ Populate a base layout that we can use """
    self.layout = Layout()
    self.layout.expires = datetime.datetime.now().isoformat()

  def test_wrong_type(self):
    """ test the type field within Validate() """
  
    with self.assertRaises(FormatError):
      self.layout._type = "wrong"
      self.layout._validate_type()
      self.assertFalse(self.layout.validate())

    self.layout._type = "layout"
    self.assertTrue(self.layout._validate_type())

  def test_wrong_expires(self):
    """ test the expires field is properly populated """

    with self.assertRaises(FormatError):
      self.layout.expires = '' 
      self.layout._validate_expires()
      self.layout.validate()

      self.layout.expires = '-1' 
      self.layout._validate_expires()
      self.layout.validate()

      # notice the wrong month 
      self.layout.expires = '2016-13-18T16:44:55.553304'
      self.layout._validate_expires()
      self.layout.validate()

    self.layout.expires = '2016-11-18T16:44:55.553304'
    self.assertTrue(self.layout._validate_expires())
    self.assertTrue(self.layout.validate())

  def test_wrong_key_dictionary(self):
    """ test that the keys dictionary is properly populated """ 
    rsa_key_one = toto.ssl_crypto.keys.generate_rsa_key()
    rsa_key_two = toto.ssl_crypto.keys.generate_rsa_key()

    with self.assertRaises(FormatError):

      # FIXME: attr.ib reutilizes the default dictionary, so future constructor
      # are not empty...
      self.layout.keys = {}
      self.layout.keys["kek"] = rsa_key_one

      self.layout._validate_keys()
      self.layout.validate()

      self.layout.keys = {}
      self.layout.keys[rsa_key_two['keyid']] = "kek"

      self.layout._validate_keys()
      self.layout.validate()

    self.layout.keys = {}
    self.layout.keys[rsa_key_one['keyid']] = rsa_key_one
    self.layout.keys[rsa_key_two['keyid']] = rsa_key_two

    self.assertTrue(self.layout._validate_keys())
    self.assertTrue(self.layout.validate())

  def test_wrong_steps_list(self):
    """ check that the validate method checks the steps' correctness """
    with self.assertRaises(FormatError):
      self.layout.steps = "not-a-step"
      self.layout.validate()

      test_step = Step("this-is-a-step")
      test_step.material_matchrules = ['this is a malformed step']
      self.layout.steps = [test_step]
      self.layout.validate()


    test_step = Step("this-is-a-step")
    test_step.material_matchrules = [["CREATE", "foo"]]
    self.layout.steps = [test_step]
    self.layout.validate()

  def test_wrong_inspect_list(self):
    """ check that the validate method checks the inspections' correctness """

    with self.assertRaises(FormatError):
      self.layout.inspect = "not-an-inspection"
      self.layout.validate()

      test_inspection = Inspection("this-is-a-step")
      test_inspection.material_matchrules = ['this is a malformed inspection']
      self.layout.inspect= [test_inspection]
      self.layout.validate()


    test_inspection = Inspection("this-is-a-step")
    test_inspection.material_matchrules = [["CREATE", "foo"]]
    self.layout.inspect = [test_inspection]
    self.layout.validate()


    pass

if __name__ == '__main__':

  unittest.main()
