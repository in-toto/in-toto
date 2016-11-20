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
    """ Populate a base layout that we can use """
    self.inspection = Inspection("some-inspection")

  def test_wrong_type(self):
    """ test the type field within Validate() """
  
    with self.assertRaises(FormatError):
      self.inspection._type = "wrong"
      self.inspection._validate_type()
      self.assertFalse(self.inspection.validate())

    self.inspection._type = "inspection"
    self.inspection._validate_type()

  def test_wrong_material_matchrules(self):
    """ test that the material matchrule validators catch malformed ones """
   
    with self.assertRaises(FormatError):
      self.inspection.material_matchrules = [["NONFOO"]]
      self.inspection._validate_material_matchrules()
      self.assertFalse(self.inspection.validate())

      self.inspection.material_matchrules = "PFF"
      self.inspection._validate_material_matchrules()
      self.assertFalse(self.inspection.validate())

    # for more thorough tests, check the test_matchrule.py module
    self.inspection.material_matchrules = [["CREATE", "foo"]]
    self.inspection._validate_material_matchrules()
    self.assertFalse(self.inspection.validate())

  def test_wrong_product_matchrules(self):
    """ test that the product matchrule validatores catch malformed ones """

    with self.assertRaises(FormatError):
      self.inspection.product_matchrules = [["NONFOO"]]
      self.inspection._validate_product_matchrules()
      self.assertFalse(self.inspection.validate())

      self.inspection.product_matchrules = "PFF"
      self.inspection._validate_product_matchrules()
      self.assertFalse(self.inspection.validate())

    # for more thorough tests, check the test_matchrule.py module
    self.inspection.product_matchrules = [["CREATE", "foo"]]
    self.inspection._validate_product_matchrules()
    self.assertFalse(self.inspection.validate())

  def test_wrong_run(self):

    with self.assertRaises(FormatError): 

      # no, python is not *this* smart
      self.inspection.run = -1

      self.inspection._validate_run()
      self.inspection.validate()

    self.inspection.run = "somecommand"
    self.inspection._validate_run()
    self.inspection.validate()

if __name__ == '__main__':

  unittest.main()
