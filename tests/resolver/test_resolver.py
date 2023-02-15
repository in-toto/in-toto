#!/usr/bin/env python

# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  test_resolver.py

<Author>
  Alan Chung Ma <achungma@purdue.edu>

<Started>
  February 1, 2023

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test resolver interface functions.

"""

import unittest
from in_toto.resolver import (Resolver, FileResolver)
from in_toto.resolver._resolver import _get_resolver


class TestGetResolver(unittest.TestCase):
  """Test _get_resolver(uri) """

  def test_get_resolver_default_scheme(self):
    uri = "some/directory"
    resolver = _get_resolver(uri)
    self.assertEqual(resolver, FileResolver)

  def test_get_resolver_file_scheme(self):
    uri = "file:some/directory"
    resolver = _get_resolver(uri)
    self.assertEqual(resolver, FileResolver)

  def test_get_resolver_invalid_uri(self):
    uri = ""
    with self.assertRaises(ValueError):
      _get_resolver(uri)

  def test_get_resolver_invalid_scheme(self):
    uri = "nonexistent:invalid/scheme"
    with self.assertRaises(ValueError):
      _get_resolver(uri)


class TestResolverApplyExcludePatterns(unittest.TestCase):
  """Test Resolver.apply_exclude_patterns(names, exclude_patterns) """

  def test_resolver_apply_exclude_explict(self):
    names = ["foo", "bar", "baz"]
    patterns = ["foo", "bar"]
    expected = ["baz"]
    result = Resolver.apply_exclude_patterns(names, patterns)
    self.assertListEqual(sorted(result), sorted(expected))

  def test_resolver_apply_exclude_all(self):
    names = ["foo", "bar", "baz"]
    patterns = ["*"]
    expected = []
    result = Resolver.apply_exclude_patterns(names, patterns)
    self.assertListEqual(sorted(result), sorted(expected))

  def test_resolver_apply_exclude_multiple_star(self):
    names = ["foo", "bar", "baz"]
    patterns = ["*a*"]
    expected = ["foo"]
    result = Resolver.apply_exclude_patterns(names, patterns)
    self.assertListEqual(result, expected)

  def test_resolver_apply_exclude_question_mark(self):
    names = ["foo", "bazfoo", "barfoo"]
    patterns = ["ba?foo"]
    expected = ["foo"]
    result = Resolver.apply_exclude_patterns(names, patterns)
    self.assertListEqual(result, expected)

  def test_resolver_apply_exclude_seq(self):
    names = ["baxfoo", "bazfoo", "barfoo"]
    patterns = ["ba[xz]foo"]
    expected = ["barfoo"]
    result = Resolver.apply_exclude_patterns(names, patterns)
    self.assertListEqual(result, expected)

  def test_resolver_apply_exclude_neg_seq(self):
    names = ["baxfoo", "bazfoo", "barfoo"]
    patterns = ["ba[!r]foo"]
    expected = ["barfoo"]
    result = Resolver.apply_exclude_patterns(names, patterns)
    self.assertListEqual(result, expected)


if __name__ == "__main__":
  unittest.main()
