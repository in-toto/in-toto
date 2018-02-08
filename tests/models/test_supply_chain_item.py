#!/usr/bin/env python
"""
<Program Name>
  test_supply_chain_item.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Jan 25, 2018

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test SupplyChainItem class methods.
  SupplyChainItem is a super class for Steps and Inspections.

"""
import json
import unittest
from in_toto.models.layout import SupplyChainItem
import securesystemslib.exceptions

class TestSupplyChainItem(unittest.TestCase):
  """Test models.SupplyChainItem. """


  def test_wrong_expected_materials(self):
    """Test that the material rule validators catch malformed ones."""
    item = SupplyChainItem()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      item.expected_materials = [["NONFOO"]]
      item._validate_expected_materials()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      item.validate()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      item.expected_materials = "PFF"
      item._validate_expected_materials()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      item.validate()

    # for more thorough tests, check the test_rulelib.py module
    item.expected_materials = [["CREATE", "foo"]]
    item._validate_expected_materials()
    item.validate()


  def test_wrong_expected_products(self):
    """Test that the product rule validators catch malformed values."""
    item = SupplyChainItem()

    item.expected_products = [["NONFOO"]]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      item._validate_expected_products()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      item.validate()

    item.expected_products = "PFF"
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      item._validate_expected_products()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      item.validate()

    # for more thorough tests, check the test_rulelib.py module
    item.expected_products = [["CREATE", "foo"]]
    item._validate_expected_products()
    item.validate()


  def test_repr(self):
    """Test repr returns a JSON parseable string. """
    json.loads(repr(SupplyChainItem()))


  def test_add_rule_from_string(self):
    """Test that add_rule_from string methods set property correctly. """
    item = SupplyChainItem()
    item.add_material_rule_from_string("CREATE foo")
    self.assertListEqual(item.expected_materials[-1], ["CREATE", "foo"])
    item.add_product_rule_from_string("ALLOW bar")
    self.assertListEqual(item.expected_products[-1], ["ALLOW", "bar"])

    item.validate()


if __name__ == "__main__":
  unittest.main()
