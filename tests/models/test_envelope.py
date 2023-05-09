#!/usr/bin/env python

# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  test_envelope.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Oct 25, 2022

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test in_toto.models.metadata.Envelope class methods.

"""

import os
import unittest

from in_toto.models.layout import Layout
from in_toto.models.link import Link
from in_toto.models.metadata import Envelope
from tests.common import TmpDirMixin


class TestMetablockValidator(unittest.TestCase, TmpDirMixin):
    """Test in_toto.models.metadata.Envelope methods."""

    def test_create_envelope(self):
        """Test DSSE envelope creation from Link or Layout."""

        # Create DSSE Envelope from empty Link.
        link = Link()
        env = Envelope.from_signable(link)

        # Verify links.
        self.assertEqual(env.get_payload(), link)

        # Create DSSE Envelope from empty Layout.
        layout = Layout()
        env = Envelope.from_signable(layout)

        # Verify layouts.
        self.assertEqual(env.get_payload(), layout)

    def test_load_envelope(self):
        """Test loading and parsing of in-toto envelope."""

        # Demo DSSE Metadata Files
        demo_dsse_files = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../demo_dsse_files"
        )

        layout_path = os.path.join(demo_dsse_files, "demo.layout.template")
        link_path = os.path.join(demo_dsse_files, "package.2f89b927.link")

        # Load layout metadata.
        env = Envelope.load(layout_path)
        layout = env.get_payload()

        self.assertIsInstance(layout, Layout)

        # Load link metadata.
        env = Envelope.load(link_path)
        link = env.get_payload()

        self.assertIsInstance(link, Link)


if __name__ == "__main__":
    unittest.main()
