#!/usr/bin/env python
"""
<Program Name>
  test_metadata.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Jan 24, 2018

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test in_toto.models.metadata.Metablock class methods.

"""

import os
import unittest

from in_toto.models.metadata import Metablock
from in_toto.models.layout import Layout
from in_toto.models.link import Link
from securesystemslib.exceptions import FormatError

class TestMetablockValidator(unittest.TestCase):
  """Test in_toto.models.metadata.Metablock validators. """

  def test_validate_signed(self):
    """Test validate Metablock's 'signed' property. """
    # Valid Layout Metablock
    metablock = Metablock(signed=Layout())
    metablock._validate_signed()

    # Valid Link Metablock
    Metablock(signed=Link())
    metablock._validate_signed()


    # Fail instantiation with empty or invalid signed property
    # Metablock is validated on instantiation
    with self.assertRaises(FormatError):
      Metablock()
    with self.assertRaises(FormatError):
      Metablock(signed="not-a-layout-or-link")


    # Fail with invalid signed property
    metablock = Metablock(signed=Layout())
    metablock.signed._type = "bogus type"
    with self.assertRaises(FormatError):
      metablock._validate_signed()


  def test_validate_signatures(self):
    """Test validate Metablock's 'signatures' property. """
    # An empty signature list is okay
    metablock = Metablock(signed=Layout())
    metablock._validate_signatures()

    # Fail with signatures property not a list
    metablock.signatures = "not-a-signatures-list"
    with self.assertRaises(FormatError):
      metablock._validate_signatures()

    # Fail with invalid signature
    metablock.signatures = []
    metablock.signatures.append("not-a-signature")
    with self.assertRaises(FormatError):
      metablock._validate_signatures()

    # Load signed demo link
    demo_link_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
        "..", "demo_files", "write-code.776a00e2.link")

    metablock = Metablock.load(demo_link_path)

    # Verify that there is a signature and that it is valid
    self.assertTrue(len(metablock.signatures) > 0)
    metablock._validate_signatures()


if __name__ == "__main__":
  unittest.main()
