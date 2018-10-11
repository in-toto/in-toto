#!/usr/bin/env python
"""
<Program Name>
  test_link.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Sep 28, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test link class functions.

"""

import unittest
from in_toto.models.link import Link
from securesystemslib.exceptions import FormatError

class TestLinkValidator(unittest.TestCase):
  """Test link format validators """

  def test_validate_type(self):
    """Test `_type` field. Must be "link" """
    test_link = Link()

    # Good type
    test_link._type = "link"
    test_link.validate()

    # Bad type
    test_link._type = "bad link"
    with self.assertRaises(FormatError):
      test_link.validate()


  def test_validate_materials(self):
    """Test `materials` field. Must be a `dict` of HASH_DICTs """
    test_link = Link()

    # Good materials
    sha = "d65165279105ca6773180500688df4bdc69a2c7b771752f0a46ef120b7fd8ec3"
    test_link.materials = {"foo": {"sha256": sha}}
    test_link.validate()

    # Bad materials 1
    test_link.materials = "not a dict"
    with self.assertRaises(FormatError):
      test_link.validate()

    # Bad materials 1
    test_link.materials = {"not": "a material dict"}
    with self.assertRaises(FormatError):
      test_link.validate()


  def test_validate_products(self):
    """Test `products` field. Must be a `dict` of HASH_DICTs """
    test_link = Link()

    # Good products
    sha = "cfdaaf1ab2e4661952a9dec5e8fa3c360c1b06b1a073e8493a7c46d2af8c504b"
    test_link.products = {"bar": {"sha256": sha}}
    test_link.validate()

    # Bad products 1
    test_link = Link()
    test_link.products = "not a dict"
    with self.assertRaises(FormatError):
      test_link.validate()

    # Bad products 2
    test_link.products = {"not": "a product dict"}
    with self.assertRaises(FormatError):
      test_link.validate()


  def test_validate_byproducts(self):
    """Test `byproducts` field. Must be a `dict` """
    test_link = Link()
    # Good byproducts
    test_link.byproducts = {}
    test_link.validate()

    # Bad byproducts
    test_link.byproducts = "not a dict"
    with self.assertRaises(FormatError):
      test_link.validate()


  def test_validate_command(self):
    """Test `command` field. Must be either a `list` """
    test_link = Link()

    # Good command
    test_link.command = ["echo", "'good command'"]
    test_link.validate()

    # Bad command
    test_link.command = "echo 'bad command'"
    with self.assertRaises(FormatError):
      test_link.validate()


  def test_validate_environment(self):
    """Test `environment` field. Must be a `dict` """
    test_link = Link()

    # good env per default
    test_link.validate()

    # Bad env
    test_link.environment = "not a dict"
    with self.assertRaises(FormatError):
      test_link.validate()
