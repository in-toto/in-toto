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

import securesystemslib.hash


class MockResolver(Resolver):

  SCHEME = "mock"

  @classmethod
  def resolve_uri_to_uris(cls, generic_uri, exclude_patterns=None):
    return generic_uri

  @classmethod
  def get_key_from_uri(cls, resolved_uri):
    return resolved_uri

  @classmethod
  def get_artifact_hashdict(cls, resolved_uri):

    digest_object = securesystemslib.hash.digest('sha256')
    digest_object.update(resolved_uri.encode('utf-8'))

    return {'sha256': digest_object.hexdigest()}


RESOLVER_FOR_URI_SCHEME.update(
  {
    MockResolver.SCHEME: MockResolver,
  }
)


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


class TestResolverInterface(unittest.TestCase):
  """Test Resolver interface."""

  def test_resolver_hash_artifact(self):
    key, hash_dict = Resolver.hash_artifact("mock:uri")
    self.assertTrue(
        "sha256" in list(hash_dict))
    self.assertEqual(key, "mock:uri")


if __name__ == "__main__":
  unittest.main()
