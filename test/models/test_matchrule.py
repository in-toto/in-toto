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
from toto.models.matchrule import check_matchrule_syntax

class TestMatchruleSyntax(unittest.TestCase):
  """Test matchrule syntax validators """

  def test_validate_generic_rules(self):

    # test for non-existing generic rule
    with self.assertRaises(FormatError):
      rule = ["SUBVERT", "foo"]
      check_matchrule_syntax(rule)

      rule = ["CREATE", "foo", "AND", "bar"]
      check_matchrule_syntax(rule)

      rule = ["CREATE"]
      check_matchrule_syntax(rule)

    # test proper generic rule
    rule = ["CREATE", "foo"]
    check_matchrule_syntax(rule)

    rule = ["MODIFY", "foo"]
    check_matchrule_syntax(rule)

    rule = ["DELETE", "foo"]
    check_matchrule_syntax(rule)
 
  def test_validate_match_rule(self):

    with self.assertRaises(FormatError):
      rule = ["MATCH"]
      check_matchrule_syntax(rule)

      rule = ["MATCH", "PRODUCT", "foo", "NOTFROM", "step"]
      check_matchrule_syntax(rule)

      rule = ["MATCH", "PRODUCT", "foo", "FROM", "step", "NOT-AS", "otherpath"]
      check_matchrule_syntax(rule)

      rule = ["MATCH", "PRODUCT", "foo", "FROM"]
      check_matchrule_syntax(rule)

      rule = ["MATCH", "PRODUCT", "foo", "FROM", "step", "NOT-AS"]
      check_matchrule_syntax(rule)

    rule = ["MATCH", "PRODUCT", "foo", "FROM", "step"]
    check_matchrule_syntax(rule)

    rule = ["MATCH", "PRODUCT", "foo", "FROM", "step", "AS", "bar"]
    check_matchrule_syntax(rule)

if __name__ == '__main__':

  unittest.main()
