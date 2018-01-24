#!/usr/bin/env python

"""
<Program Name>
  models/test_artifact_rules.py

<Author>
  Santiago Torres-Arias <santiago@nyu.edu>

<Started>
  Nov 19, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test artifact rule unpacking.

"""
import unittest
from in_toto.artifact_rules import unpack_rule
import securesystemslib.exceptions


class TestArtifactRuleUnpack(unittest.TestCase):
  """Test artifact rule unpacker/syntax checker. """

  def test_unpack_rule_not_list(self):
    """Test rule syntax error, not a list. """

    rule = "CREATE stuff"
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      unpack_rule(rule)

  def test_unpack_rule_not_enough_keywords(self):
    """Test rule syntax error, too little arguments. """
    rule = ["DELETE"]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      unpack_rule(rule)

  def test_unpack_rule_unknown_rule_type(self):
    """Test generic rule syntax error, too many arguments. """
    rule = ["SUBVERT", "foo"]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      unpack_rule(rule)

  def test_unpack_rule_pattern_not_string(self):
    """Test rule syntax error, pattern not a string. """
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      rule = ["CREATE", {"abc"}]
      unpack_rule(rule)

  def test_unpack_generic_rule_too_long(self):
    """Test generic rule syntax error, too many arguments. """
    rule = ["CREATE", "foo", "pleaze!!"]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      unpack_rule(rule)

  def test_unpack_generic_rule(self):
    """Test generic rule proper unpacking. """
    rule = ["CREATE", "foo"]
    rule_data = unpack_rule(rule)
    self.assertEquals(len(list(rule_data.keys())), 2)
    self.assertEquals(rule_data["rule_type"], "create")
    self.assertEquals(rule_data["pattern"], "foo")

    rule = ["DELETE", "foo"]
    rule_data = unpack_rule(rule)
    self.assertEquals(len(list(rule_data.keys())), 2)
    self.assertEquals(rule_data["rule_type"], "delete")
    self.assertEquals(rule_data["pattern"], "foo")

    rule = ["MODIFY", "foo"]
    rule_data = unpack_rule(rule)
    self.assertEquals(len(list(rule_data.keys())), 2)
    self.assertEquals(rule_data["rule_type"], "modify")
    self.assertEquals(rule_data["pattern"], "foo")

    rule = ["ALLOW", "foo"]
    rule_data = unpack_rule(rule)
    self.assertEquals(len(list(rule_data.keys())), 2)
    self.assertEquals(rule_data["rule_type"], "allow")
    self.assertEquals(rule_data["pattern"], "foo")

    rule = ["DISALLOW", "foo"]
    rule_data = unpack_rule(rule)
    self.assertEquals(len(list(rule_data.keys())), 2)
    self.assertEquals(rule_data["rule_type"], "disallow")
    self.assertEquals(rule_data["pattern"], "foo")


  def test_unpack_match_rule(self):
    """Check match rule proper unpacking. """

    rule = ["MATCH", "foo", "IN", "source-path", "WITH",
        "PRODUCTS", "IN", "dest-path", "FROM", "step-name"]
    rule_data = unpack_rule(rule)
    self.assertEquals(len(list(rule_data.keys())), 6)
    self.assertEquals(rule_data["rule_type"], "match")
    self.assertEquals(rule_data["pattern"], "foo")
    self.assertEquals(rule_data["source_prefix"], "source-path")
    self.assertEquals(rule_data["dest_prefix"], "dest-path")
    self.assertEquals(rule_data["dest_type"], "products")
    self.assertEquals(rule_data["dest_name"], "step-name")

    rule = ["MATCH", "foo", "IN", "source-path", "WITH",
        "MATERIALS", "FROM", "step-name"]
    rule_data = unpack_rule(rule)
    self.assertEquals(len(list(rule_data.keys())), 6)
    self.assertEquals(rule_data["rule_type"], "match")
    self.assertEquals(rule_data["pattern"], "foo")
    self.assertEquals(rule_data["source_prefix"], "source-path")
    self.assertEquals(rule_data["dest_prefix"], "")
    self.assertEquals(rule_data["dest_type"], "materials")
    self.assertEquals(rule_data["dest_name"], "step-name")

    rule = ["MATCH", "foo", "WITH",
        "PRODUCTS", "IN", "dest-path", "FROM", "step-name"]
    rule_data = unpack_rule(rule)
    self.assertEquals(len(list(rule_data.keys())), 6)
    self.assertEquals(rule_data["rule_type"], "match")
    self.assertEquals(rule_data["pattern"], "foo")
    self.assertEquals(rule_data["source_prefix"], "")
    self.assertEquals(rule_data["dest_prefix"], "dest-path")
    self.assertEquals(rule_data["dest_type"], "products")
    self.assertEquals(rule_data["dest_name"], "step-name")

    rule = ["MATCH", "foo", "WITH",
        "PRODUCTS", "FROM", "step-name"]
    rule_data = unpack_rule(rule)
    self.assertEquals(len(list(rule_data.keys())), 6)
    self.assertEquals(rule_data["rule_type"], "match")
    self.assertEquals(rule_data["pattern"], "foo")
    self.assertEquals(rule_data["source_prefix"], "")
    self.assertEquals(rule_data["dest_prefix"], "")
    self.assertEquals(rule_data["dest_type"], "products")
    self.assertEquals(rule_data["dest_name"], "step-name")

  def test_unpack_match_rule_wrong_length(self):
    """Check match rule syntax error, too few or many arguments. """

    rule = ["MATCH", "foo", "WITH", "PRODUCTS", "FROM"]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      unpack_rule(rule)

    rule = ["MATCH", "foo", "WITH", "PRODUCTS", "FROM", "step-name", "really?"]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      unpack_rule(rule)

    rule = ["MATCH", "foo", "IN", "source-path", "WITH",
        "PRODUCTS", "IN", "dest-path", "FROM", "step-name", "YES, we can!"]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      unpack_rule(rule)

  def test_unpack_match_rule_wrong_types(self):
    """Check match rule syntax error, wrong data type in variable arguments. """
    # pattern must be string
    rule = ["MATCH", ["abc"], "IN", "source-path", "WITH",
        "PRODUCTS", "IN", "dest-path", "FROM", "step-name"]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      unpack_rule(rule)

    # source path must be a string
    rule = ["MATCH", "foo", "IN", {"abc": "def"}, "WITH",
        "PRODUCTS", "IN", "dest-path", "FROM", "step-name"]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      unpack_rule(rule)

    # dest-path must be a string
    rule = ["MATCH", "foo", "IN", "source-path", "WITH",
        "PRODUCTS", "IN", 123, "FROM", "step-name"]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      unpack_rule(rule)

    # step-name must be a string
    rule = ["MATCH", "foo", "IN", "source-path", "WITH",
        "PRODUCTS", "IN", "dest-path", "FROM", ("456",)]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      unpack_rule(rule)

  def test_unpack_match_rule_wrong_destination_type(self):
    """Check match rule syntax error, wrong destination type. """
    rule = ["MATCH", "foo", "IN", "source-path", "WITH",
        "PONIES", "IN", "dest-path", "FROM", "step-name"]
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      unpack_rule(rule)

if __name__ == "__main__":

  unittest.main()
