#!/usr/bin/env python

# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  test_provenance.py

<Author>
  Furkan Türkal <furkan.turkal@trendyol.com>

<Started>
  Aug 3, 2021

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test provenance class functions.

"""

import unittest
from in_toto.models.provenance import Provenance
from securesystemslib.exceptions import FormatError


class TestProvenanceValidator(unittest.TestCase):
  """Test provenance format validators """

  def test_validate_type(self):
    """Test `_type` field. Must be "provenance" """
    test = Provenance()

    # Good type
    test._type = "provenance"
    test.validate()

    # Bad type
    test._type = "bad link"
    with self.assertRaises(FormatError):
      test.validate()

  def test_validate_builder(self):
    """Test `builder` field. Must be a `dict`"""
    test = Provenance()

    # Good builder
    test.builder = {"id": "https://foo.bar/baz"}
    test.validate()

    # Bad builder 1
    test.builder = "not a dict"
    with self.assertRaises(FormatError):
      test.validate()

    # Bad builder 2
    test.builder = {"id": 15}
    with self.assertRaises(FormatError):
      test.validate()

  def test_validate_recipe(self):
    """Test `recipe` field. Must be a `dict`"""
    test = Provenance()

    # Good products
    test.recipe = {"type": "foo", "definedInMaterial": 0, "entryPoint": "", "arguments": {}, "environment": {}}
    test.validate()

    # Bad recipe 1
    test = Provenance()
    test.recipe = "not a dict"
    with self.assertRaises(FormatError):
      test.validate()

    # Bad recipe 2: non-exist required type field
    test.recipe = {"not": "type must exist"}
    with self.assertRaises(AssertionError):
      test.validate()

    # Bad recipe 3: non-string entryPoint
    test.recipe = {"type": "foo", "definedInMaterial": 0, "entryPoint": 15, "arguments": {}, "environment": {}}
    with self.assertRaises(FormatError):
      test.validate()

    # Bad recipe 4: non-obj arguments
    test.recipe = {"type": "foo", "definedInMaterial": 0, "entryPoint": "", "arguments": [], "environment": {}}
    with self.assertRaises(FormatError):
      test.validate()

    # Bad recipe 5: non-obj environment
    test.recipe = {"type": "foo", "definedInMaterial": 0, "entryPoint": "", "arguments": {}, "environment": []}
    with self.assertRaises(FormatError):
      test.validate()

  def test_validate_metadata(self):
    """Test `metadata` field. Must be a `list`"""
    test = Provenance()

    # Good metadata 1
    test.metadata = {"buildInvocationId": "", "buildStartedOn": 1628017067, "buildFinishedOn": 1628017089, "reproducible": False, "completeness": {"arguments": False, "environment": False, "materials": False}}
    test.validate()

    # Good metadata 2: all optional
    test.metadata = {}
    test.validate()

    # Bad metadata 1
    test.metadata = "not a obj"
    with self.assertRaises(FormatError):
      test.validate()

    # Bad metadata 2: non-string buildInvocationId
    test.metadata = {"buildInvocationId": 15}
    with self.assertRaises(FormatError):
      test.validate()

    # Bad metadata 3: non-unix-format buildStartedOn
    test.metadata = {"buildStartedOn": -707}
    with self.assertRaises(FormatError):
      test.validate()

    # Bad metadata 4: non-unix-format buildFinishedOn
    test.metadata = {"buildFinishedOn": -707}
    with self.assertRaises(FormatError):
      test.validate()

    # Bad metadata 5: non-bool reproducible
    test.metadata = {"reproducible": "foo"}
    with self.assertRaises(FormatError):
      test.validate()

    # Bad metadata 6: non-obj completeness
    test.metadata = {"completeness": []}
    with self.assertRaises(AttributeError):
      test.validate()

    # Bad metadata 7: non-bool completeness.arguments
    test.metadata = {"completeness": {"arguments": "foo"}}
    with self.assertRaises(FormatError):
      test.validate()

    # Bad metadata 8: non-bool completeness.environment
    test.metadata = {"completeness": {"environment": "foo"}}
    with self.assertRaises(FormatError):
      test.validate()

    # Bad metadata 9: non-bool completeness.materials
    test.metadata = {"completeness": {"materials": "foo"}}
    with self.assertRaises(FormatError):
      test.validate()

  def test_validate_materials(self):
    """Test `materials` field. Must be a `list`"""
    test = Provenance()

    # Good materials
    test.materials = [{"uri": "foo", "digest": {"md5": "8f961ea23d77b9b8c01a12b2818e1055"}}]
    test.validate()

    # Bad materials 1
    test.materials = "not a list"
    with self.assertRaises(FormatError):
      test.validate()

    # Bad materials 2: non-string uri, optional digest
    test.materials = [{"uri": 15}]
    with self.assertRaises(FormatError):
      test.validate()

    # Bad materials 3: bad digest format
    test.materials = [{"uri": "bar", "digest": "baz"}]
    with self.assertRaises(FormatError):
      test.validate()
