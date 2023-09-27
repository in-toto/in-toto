#!/usr/bin/env python

# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  test_common.py

<Author>
  Santiago Torres-Arias <santiago@nyu.edu>

<Started>
  Sept 26, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test the Signable and ValidationMixin class functions.

"""

import json
import textwrap
import unittest
from collections import OrderedDict

from in_toto.models.common import (
    Signable,
    BeautifyMixin,
)


class TestSignable(unittest.TestCase):
    """Verifies Signable class."""

    def test_load_repr_string_as_json(self):
        """Test load string returned by `Signable.repr` as JSON"""
        json.loads(repr(Signable()))


class TestBeautifyMixin(unittest.TestCase):
    """Tests BeautifyMixin's beautify method"""

    class ExampleMetadata(BeautifyMixin):
        """Metadata class to mock real metadata instances for testing"""
        def get_beautify_dict(self, order=None):
            """Organize Layout's metadata attributes as key-value pairs"""
            metadata = OrderedDict({
                "field_string": "value",
                "field_integer": 1,
                "field_list_string": ["value1", "value2", "value3"],
                "field_list_integer": [1, 2, 3],
                "field_dict": {
                    "field_string": "value",
                    "field_integer": 1,
                    "field_list": ["value"],
                    "field_nested_dict": {
                        "field_string": "value",
                        "field_integer": 1,
                        "field_list": ["value"],
                    }
                }
            })

            if not order:
                return metadata
            
            ordered_metadata = {}
            for field in order:
                ordered_metadata[field] = metadata[field]
            return ordered_metadata

    def test_beautify(self):
        metadata = self.ExampleMetadata()
        beautified_metadata = metadata.beautify()
        expected = textwrap.dedent(
            """
            field_string: value
            field_integer: 1
            field_list_string: 
                value1
                value2
                value3
            field_list_integer: 
                1
                2
                3
            field_dict: 
                field_string: value
                field_integer: 1
                field_list: 
                    value
                field_nested_dict: 
                    field_string: value
                    field_integer: 1
                    field_list: 
                        value
            """
        ).strip()
        self.assertEqual(beautified_metadata, expected)

    def test_beautify_with_order(self):
        metadata = self.ExampleMetadata()
        order = ["field_dict", "field_integer", "field_string"]
        beautified_metadata = metadata.beautify(order)
        expected = textwrap.dedent(
            """
            field_dict: 
                field_string: value
                field_integer: 1
                field_list: 
                    value
                field_nested_dict: 
                    field_string: value
                    field_integer: 1
                    field_list: 
                        value
            field_integer: 1
            field_string: value
            """
        ).strip()
        self.assertEqual(beautified_metadata, expected)


if __name__ == "__main__":
    unittest.main()
