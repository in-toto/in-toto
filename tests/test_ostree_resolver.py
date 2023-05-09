#!/usr/bin/env python
# coding=utf-8

# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  test_ostree_resolver.py

<Author>
  Aditya Sirish A Yelgundhalli <aditya.sirish@nyu.edu>

<Started>
  May 04, 2023

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test OSTree resolver.

"""

import os
import unittest
from pathlib import Path

from in_toto.resolver import OSTreeResolver


class TestOSTreeResolver(unittest.TestCase):
    """Test OSTree resolver implementation."""

    def test_hash_for_branch_with_base_path(self):
        """Verify hash of test-branch with base_path."""

        resolver = OSTreeResolver(
            base_path=str(Path(__file__).parent / "resolver" / "ostree_repo")
        )

        uri = "ostree:test-branch"

        expected_artifact_dict = {
            uri: {
                "sha256": "cf3e103a6aed64aec261e2161d1026aa26349d422d238b1ad9e2e2a7eeed8591"
            }
        }

        artifact_dict = resolver.hash_artifacts([uri])
        self.assertEqual(artifact_dict, expected_artifact_dict)

    def test_hash_for_branch_with_cwd(self):
        """Verify hash of test-branch from ostree_repo in current dir."""

        current_dir = os.getcwd()

        os.chdir(Path(__file__).parent / "resolver" / "ostree_repo")
        resolver = OSTreeResolver()

        uri = "ostree:test-branch"

        expected_artifact_dict = {
            uri: {
                "sha256": "cf3e103a6aed64aec261e2161d1026aa26349d422d238b1ad9e2e2a7eeed8591"
            }
        }

        artifact_dict = resolver.hash_artifacts([uri])
        self.assertEqual(artifact_dict, expected_artifact_dict)

        os.chdir(current_dir)

    def test_non_existent_ref(self):
        """Verify expected exception for non existent ref."""

        resolver = OSTreeResolver(
            base_path=str(Path(__file__).parent / "resolver" / "ostree_repo")
        )
        uri = "ostree:invalid"
        with self.assertRaises(FileNotFoundError):
            resolver.hash_artifacts([uri])

    def test_non_existent_ostree_repo(self):
        """Verify expected exception for non existent repo."""

        resolver = OSTreeResolver(
            base_path=str(Path(__file__).parent / "resolver" / "not_a_repo")
        )

        with self.assertRaises(FileNotFoundError):
            resolver.hash_artifacts(["ostree:some-ref"])


if __name__ == "__main__":
    unittest.main()
