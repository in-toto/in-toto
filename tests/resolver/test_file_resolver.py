#!/usr/bin/env python

# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  test_file_resolver.py

<Author>
  Alan Chung Ma <achungma@purdue.edu>

<Started>
  April 17, 2023

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test file resolver helper and interface functions.

"""

import unittest
from in_toto.resolver.file_resolver import (apply_exclude_patterns,
                                            apply_left_strip)


class TestApplyLeftStrip(unittest.TestCase):
  """Test apply_left_strip"""

  def test_apply_left_strip_no_scheme(self):
    uri = "lstrip-value/name"
    lstrip_paths = ["lstrip-value/"]
    self.assertEqual(apply_left_strip(uri, lstrip_paths), "name")

  def test_apply_left_strip_with_scheme(self):
    uri = "file:lstrip-value/name"
    lstrip_paths = ["lstrip-value/"]
    self.assertEqual(apply_left_strip(uri, lstrip_paths), "file:name")


class TestFileResolverApplyExcludePatterns(unittest.TestCase):
  """Test apply_exclude_patterns(names, exclude_patterns) """

  def test_resolver_apply_exclude_explict(self):
    names = ["foo", "bar", "baz"]
    patterns = ["foo", "bar"]
    expected = ["baz"]
    result = apply_exclude_patterns(names, patterns)
    self.assertListEqual(sorted(result), sorted(expected))

  def test_resolver_apply_exclude_all(self):
    names = ["foo", "bar", "baz"]
    patterns = ["*"]
    expected = []
    result = apply_exclude_patterns(names, patterns)
    self.assertListEqual(sorted(result), sorted(expected))

  def test_resolver_apply_exclude_multiple_star(self):
    names = ["foo", "bar", "baz"]
    patterns = ["*a*"]
    expected = ["foo"]
    result = apply_exclude_patterns(names, patterns)
    self.assertListEqual(result, expected)

  def test_resolver_apply_exclude_question_mark(self):
    names = ["foo", "bazfoo", "barfoo"]
    patterns = ["ba?foo"]
    expected = ["foo"]
    result = apply_exclude_patterns(names, patterns)
    self.assertListEqual(result, expected)

  def test_resolver_apply_exclude_seq(self):
    names = ["baxfoo", "bazfoo", "barfoo"]
    patterns = ["ba[xz]foo"]
    expected = ["barfoo"]
    result = apply_exclude_patterns(names, patterns)
    self.assertListEqual(result, expected)

  def test_resolver_apply_exclude_neg_seq(self):
    names = ["baxfoo", "bazfoo", "barfoo"]
    patterns = ["ba[!r]foo"]
    expected = ["barfoo"]
    result = apply_exclude_patterns(names, patterns)
    self.assertListEqual(result, expected)
