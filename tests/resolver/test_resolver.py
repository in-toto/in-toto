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
from in_toto.resolver import (Resolver, FileResolver, RESOLVER_FOR_URI_SCHEME)
from in_toto.resolver.resolver import _get_resolver
from in_toto.exceptions import ResolverGetRepresentationError

import securesystemslib.hash


class MockResolver(Resolver):

  SCHEME = "mock"

  @classmethod
  def resolve_uri_to_uris(cls, generic_uri, exclude_patterns=None):
    return generic_uri

  @classmethod
  def hash_artifact(cls, resolved_uri):

    digest_object = securesystemslib.hash.digest('sha256')
    digest_object.update(resolved_uri.encode('utf-8'))

    return {'sha256': digest_object.hexdigest()}


RESOLVER_FOR_URI_SCHEME.update(
  {
    MockResolver.SCHEME: MockResolver,
  }
)


class TestApplyLeftStrip(unittest.TestCase):

  def test_apply_left_strip_no_scheme(self):
    uri = "lstrip-value/name"
    lstrip_paths = ["lstrip-value/"]
    self.assertEqual(Resolver.apply_left_strip(uri, lstrip_paths), "name")

  def test_apply_left_strip_with_scheme(self):
    uri = "file:lstrip-value/name"
    lstrip_paths = ["lstrip-value/"]
    self.assertEqual(Resolver.apply_left_strip(uri, lstrip_paths), "file:name")


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


class TestResolverInterface(unittest.TestCase):
  """Test Resolver interface."""

  def test_resolver_get_hashable_representation_not_impl(self):
    self.assertRaises(ResolverGetRepresentationError,
                      Resolver.get_hashable_representation, "mock:uri")

  def test_resolver_hash_artifact(self):
    self.assertTrue(
        "sha256" in list(Resolver.hash_artifact("mock:uri")))


class TestResolverHashBytes(unittest.TestCase):
  """Test Resolver.hash_bytes()."""

  def test_hash_artifact_passing_algorithm(self):
    self.assertTrue(
        "sha256" in list(Resolver.hash_bytes("foo".encode('utf-8'), ["sha256"])))


if __name__ == "__main__":
  unittest.main()
