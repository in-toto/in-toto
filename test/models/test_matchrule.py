#!/usr/bin/env python

"""
<Program Name>
  models/test_matchrules.py

<Author>
  Santiago Torres-Arias <santiago@nyu.edu>

<Started>
  Nov 19, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test matchrule relevant functions.

"""

import unittest
from toto.ssl_commons.exceptions import FormatError
from toto.matchrule_validators import check_matchrule_syntax

class TestMatchruleSyntax(unittest.TestCase):
  """Test matchrule syntax validators """

  def test_validate_generic_rules(self):
    """Check the syntax generic rules (2 argument): CREATE, MODIFY, DELETE."""

    # test for non-existing generic rule
    rule = ["SUBVERT", "foo"]
    with self.assertRaises(FormatError):
      check_matchrule_syntax(rule)

    rule = ["CREATE", "foo", "AND", "bar"]
    with self.assertRaises(FormatError):
      check_matchrule_syntax(rule)

    rule = ["CREATE"]
    with self.assertRaises(FormatError):
      check_matchrule_syntax(rule)

    # test proper generic rule
    rule = ["CREATE", "foo"]
    check_matchrule_syntax(rule)

    rule = ["MODIFY", "foo"]
    check_matchrule_syntax(rule)

    rule = ["DELETE", "foo"]
    check_matchrule_syntax(rule)

  def test_validate_match_rule(self):
    """Check the MATCH variant of the matchrules."""

    rule = ["MATCH"]
    with self.assertRaises(FormatError):
      check_matchrule_syntax(rule)

    rule = ["MATCH", "PRODUCT", "foo", "NOTFROM", "step"]
    with self.assertRaises(FormatError):
      check_matchrule_syntax(rule)

    rule = ["MATCH", "PRODUCT", "foo", "NOT-AS", "otherpath", "FROM", "step"]
    with self.assertRaises(FormatError):
      check_matchrule_syntax(rule)

    rule = ["MATCH", "PRODUCT", "foo", "FROM"]
    with self.assertRaises(FormatError):
      check_matchrule_syntax(rule)

    rule = ["MATCH", "PRODUCT", "foo", "AS", "FROM", "step"]
    with self.assertRaises(FormatError):
      check_matchrule_syntax(rule)

    rule = ["MATCH", "PRODUCT", "foo", "FROM", "step"]
    check_matchrule_syntax(rule)

    rule = ["MATCH", "PRODUCT", "foo", "AS", "bar", "FROM", "step"]
    check_matchrule_syntax(rule)

if __name__ == '__main__':

  unittest.main()
