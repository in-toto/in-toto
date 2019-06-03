#!/usr/bin/env python

"""
<Program Name>
  test_rulelib.py

<Author>
  Santiago Torres-Arias <santiago@nyu.edu>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Nov 19, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test artifact rule packing and unpacking.

"""
import unittest
from in_toto.rulelib import (unpack_rule, pack_rule, pack_rule_data,
    pack_create_rule, pack_delete_rule, pack_modify_rule, pack_allow_rule,
    pack_disallow_rule, pack_require_rule)
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

  def test_unpack_and_pack_generic_rule(self):
    """Test generic rule proper packing and unpacking. """
    rule = ["CREATE", "foo"]
    rule_data = unpack_rule(rule)
    self.assertEqual(len(list(rule_data.keys())), 2)
    self.assertEqual(rule_data["rule_type"], "create")
    self.assertEqual(rule_data["pattern"], "foo")

    self.assertEqual(rule, pack_rule_data(rule_data))
    self.assertEqual(rule, pack_create_rule("foo"))


    rule = ["DELETE", "foo"]
    rule_data = unpack_rule(rule)
    self.assertEqual(len(list(rule_data.keys())), 2)
    self.assertEqual(rule_data["rule_type"], "delete")
    self.assertEqual(rule_data["pattern"], "foo")

    self.assertEqual(rule, pack_rule_data(rule_data))
    self.assertEqual(rule, pack_delete_rule("foo"))


    rule = ["MODIFY", "foo"]
    rule_data = unpack_rule(rule)
    self.assertEqual(len(list(rule_data.keys())), 2)
    self.assertEqual(rule_data["rule_type"], "modify")
    self.assertEqual(rule_data["pattern"], "foo")

    self.assertEqual(rule, pack_rule_data(rule_data))
    self.assertEqual(rule, pack_modify_rule("foo"))


    rule = ["ALLOW", "foo"]
    rule_data = unpack_rule(rule)
    self.assertEqual(len(list(rule_data.keys())), 2)
    self.assertEqual(rule_data["rule_type"], "allow")
    self.assertEqual(rule_data["pattern"], "foo")

    self.assertEqual(rule, pack_rule_data(rule_data))
    self.assertEqual(rule, pack_allow_rule("foo"))


    rule = ["DISALLOW", "foo"]
    rule_data = unpack_rule(rule)
    self.assertEqual(len(list(rule_data.keys())), 2)
    self.assertEqual(rule_data["rule_type"], "disallow")
    self.assertEqual(rule_data["pattern"], "foo")

    self.assertEqual(rule, pack_rule_data(rule_data))
    self.assertEqual(rule, pack_disallow_rule("foo"))

    rule = ["REQUIRE", "foo"]
    rule_data = unpack_rule(rule)
    self.assertEqual(len(list(rule_data.keys())), 2)
    self.assertEqual(rule_data["rule_type"], "require")
    self.assertEqual(rule_data["pattern"], "foo")

    self.assertEqual(rule, pack_rule_data(rule_data))
    self.assertEqual(rule, pack_require_rule("foo"))


  def test_unpack_and_pack_match_rule(self):
    """Check match rule proper packing and unpacking. """

    rule = ["MATCH", "foo", "IN", "source-path", "WITH",
        "PRODUCTS", "IN", "dest-path", "FROM", "step-name"]
    rule_data = unpack_rule(rule)
    self.assertEqual(len(list(rule_data.keys())), 6)
    self.assertEqual(rule_data["rule_type"], "match")
    self.assertEqual(rule_data["pattern"], "foo")
    self.assertEqual(rule_data["source_prefix"], "source-path")
    self.assertEqual(rule_data["dest_prefix"], "dest-path")
    self.assertEqual(rule_data["dest_type"], "products")
    self.assertEqual(rule_data["dest_name"], "step-name")

    self.assertEqual(rule, pack_rule_data(rule_data))
    self.assertEqual(rule, pack_rule("MATCH", "foo",
        source_prefix="source-path", dest_type="PRODUCTS",
        dest_prefix="dest-path", dest_name="step-name"))


    rule = ["MATCH", "foo", "IN", "source-path", "WITH",
        "MATERIALS", "FROM", "step-name"]
    rule_data = unpack_rule(rule)
    self.assertEqual(len(list(rule_data.keys())), 6)
    self.assertEqual(rule_data["rule_type"], "match")
    self.assertEqual(rule_data["pattern"], "foo")
    self.assertEqual(rule_data["source_prefix"], "source-path")
    self.assertEqual(rule_data["dest_prefix"], "")
    self.assertEqual(rule_data["dest_type"], "materials")
    self.assertEqual(rule_data["dest_name"], "step-name")

    self.assertEqual(rule, pack_rule_data(rule_data))
    self.assertEqual(rule, pack_rule("MATCH", "foo",
        source_prefix="source-path", dest_type="MATERIALS",
        dest_name="step-name"))


    rule = ["MATCH", "foo", "WITH",
        "PRODUCTS", "IN", "dest-path", "FROM", "step-name"]
    rule_data = unpack_rule(rule)
    self.assertEqual(len(list(rule_data.keys())), 6)
    self.assertEqual(rule_data["rule_type"], "match")
    self.assertEqual(rule_data["pattern"], "foo")
    self.assertEqual(rule_data["source_prefix"], "")
    self.assertEqual(rule_data["dest_prefix"], "dest-path")
    self.assertEqual(rule_data["dest_type"], "products")
    self.assertEqual(rule_data["dest_name"], "step-name")

    self.assertEqual(rule, pack_rule_data(rule_data))
    self.assertEqual(rule, pack_rule("MATCH", "foo",
        dest_type="PRODUCTS", dest_prefix="dest-path", dest_name="step-name"))

    rule = ["MATCH", "foo", "WITH", "PRODUCTS", "FROM", "step-name"]
    rule_data = unpack_rule(rule)
    self.assertEqual(len(list(rule_data.keys())), 6)
    self.assertEqual(rule_data["rule_type"], "match")
    self.assertEqual(rule_data["pattern"], "foo")
    self.assertEqual(rule_data["source_prefix"], "")
    self.assertEqual(rule_data["dest_prefix"], "")
    self.assertEqual(rule_data["dest_type"], "products")
    self.assertEqual(rule_data["dest_name"], "step-name")

    self.assertEqual(rule, pack_rule_data(rule_data))
    self.assertEqual(rule, pack_rule("MATCH", "foo",
        dest_type="PRODUCTS", dest_name="step-name"))

  def test_pack_rule_wrong_types(self):
    """Test argument validation for pack_rule. """
    # pattern must be a string
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      pack_rule("match", None)

    # rule_type must be a string...
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      pack_rule(1, "foo")

    # ... and one of the allowed rule types
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      pack_rule("not-a-rule-type", "foo")

    # For match rules a dest_type must be passed ...
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      pack_rule("match", "foo", dest_name="step-name")

    # ... and be one of materials or products
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      pack_rule("match", "foo", dest_type="not-a-dest-type",
          dest_name="step-name")

    # For match rules dest_name must be a string ...
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      pack_rule("match", "foo", dest_type="materials",
          dest_name=1)

    # ... and non-empty
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      pack_rule("match", "foo", dest_type="materials",
          dest_name="")

    # For match rules, if a source_prefix is passed it must be a string
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      pack_rule("match", "foo", source_prefix=1, dest_type="products",
          dest_prefix="dest-path", dest_name="step-name")

   # For match rules, if a dest_prefix is passed it must be a string
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      pack_rule("match", "foo", dest_type="products",
          dest_prefix=["not-a-string"], dest_name="step-name")


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
