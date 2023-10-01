#!/usr/bin/env python

# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

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
# pylint: disable=protected-access

import json
import os
import unittest
from collections import OrderedDict

from securesystemslib.exceptions import FormatError

from in_toto.models.common import LinkMetadataFields
from in_toto.models.link import Link


class TestLinkValidator(unittest.TestCase):
    """Test link format validators"""

    @classmethod
    def setUpClass(cls):
        cls.demo_files = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../demo_files"
        )
        cls.package_link_file = "package.2f89b927.link"

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
        """Test `materials` field. Must be a `dict` of HASH_DICTs"""
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
        """Test `products` field. Must be a `dict` of HASH_DICTs"""
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
        """Test `byproducts` field. Must be a `dict`"""
        test_link = Link()
        # Good byproducts
        test_link.byproducts = {}
        test_link.validate()

        # Bad byproducts
        test_link.byproducts = "not a dict"
        with self.assertRaises(FormatError):
            test_link.validate()

    def test_validate_command(self):
        """Test `command` field. Must be either a `list`"""
        test_link = Link()

        # Good command
        test_link.command = ["echo", "'good command'"]
        test_link.validate()

        # Bad command
        test_link.command = "echo 'bad command'"
        with self.assertRaises(FormatError):
            test_link.validate()

    def test_validate_environment(self):
        """Test `environment` field. Must be a `dict`"""
        test_link = Link()

        # good env per default
        test_link.validate()

        # Bad env
        test_link.environment = "not a dict"
        with self.assertRaises(FormatError):
            test_link.validate()

    def test_get_beautify_dict(self):
        with open(
            os.path.join(self.demo_files, self.package_link_file),
            encoding="utf8",
        ) as fptr:
            raw_json = json.load(fptr)
            link = Link().read(raw_json.get("signed"))

        expected = OrderedDict(
            {
                "Type": "link",
                "Name": "package",
                "Command": "tar zcvf foo.tar.gz foo.py",
                "Materials": {
                    "foo.py": {
                        "sha256": "74dc3727c6e89308b39e4dfedf787e37841198b1fa165a27c013544a60502549"
                    }
                },
                "Products": {
                    "foo.tar.gz": {
                        "sha256": "52947cb78b91ad01fe81cd6aef42d1f6817e92b9e6936c1e5aabb7c98514f355"
                    }
                },
                "Byproducts": {
                    "return-value": 0,
                    "stderr": "a foo.py\n",
                    "stdout": "",
                },
                "Environment": {},
            }
        )
        metadata_dict = link.get_beautify_dict()

        # Verify order of the metadata fields
        self.assertEqual(list(metadata_dict.keys()), list(expected.keys()))

        # Verify equality of all the metadata fields
        for field in metadata_dict:
            self.assertEqual(metadata_dict[field], expected[field])

    def test_get_beautify_dict_with_order(self):
        with open(
            os.path.join(self.demo_files, self.package_link_file),
            encoding="utf8",
        ) as fptr:
            raw_json = json.load(fptr)
            link = Link().read(raw_json.get("signed"))

        order = [
            LinkMetadataFields.MATERIALS,
            LinkMetadataFields.TYPE,
            LinkMetadataFields.BYPRODUCTS,
            LinkMetadataFields.NAME,
            LinkMetadataFields.COMMAND,
        ]
        expected = OrderedDict(
            {
                "Materials": {
                    "foo.py": {
                        "sha256": "74dc3727c6e89308b39e4dfedf787e37841198b1fa165a27c013544a60502549"
                    }
                },
                "Type": "link",
                "Byproducts": {
                    "return-value": 0,
                    "stderr": "a foo.py\n",
                    "stdout": "",
                },
                "Name": "package",
                "Command": "tar zcvf foo.tar.gz foo.py",
            }
        )
        metadata_dict = link.get_beautify_dict(order=order)

        # Verify order of the metadata fields
        self.assertEqual(list(metadata_dict.keys()), list(expected.keys()))

        # Verify equality of all the metadata fields
        for field in metadata_dict:
            self.assertEqual(metadata_dict[field], expected[field])
