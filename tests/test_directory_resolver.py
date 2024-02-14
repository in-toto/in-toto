"""Test cases for DirectoryResolver."""

#!/usr/bin/env python
# coding=utf-8

# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0


import os
import tempfile
import unittest
from pathlib import Path

from in_toto.exceptions import PrefixError
from in_toto.resolver import DirectoryResolver


class TestDirectoryResolver(unittest.TestCase):
    """Test directory resolver implementation."""

    def _mangle_path(self, path):
        return path.replace("\\", "/")

    def test_regular_directory(self):
        path = str(Path(__file__).parent / "resolver" / "dir_resolver")

        resolver = DirectoryResolver(normalize_line_endings=True)
        uri = f"dir:{path}"
        expected_uri = self._mangle_path(uri)

        # Expected hash calculated using:
        # find . -type f | cut -c3- | LC_ALL=C sort | xargs -r sha256sum | sha256sum | cut -f1 -d' '
        expected_artifact_dict = {
            expected_uri: {
                "sha256": "ecdbcdc6bd5d2966ad1f7595874fcd6f505abd3feaa97e27bae74bcb78c38e54"
            }
        }

        artifact_dict = resolver.hash_artifacts([uri])
        self.assertEqual(artifact_dict, expected_artifact_dict)

    def test_regular_directory_with_lstrip(self):
        lstrip_path = (
            f"{self._mangle_path(str(Path(__file__).parent))}/resolver/"
        )
        target_path = str(Path(__file__).parent / "resolver" / "dir_resolver")

        resolver = DirectoryResolver(
            lstrip_paths=[lstrip_path],
            normalize_line_endings=True,
        )

        full_uri = f"dir:{target_path}"
        stripped_uri = "dir:dir_resolver"

        # Expected hash calculated using:
        # find . -type f | cut -c3- | LC_ALL=C sort | xargs -r sha256sum | sha256sum | cut -f1 -d' '
        expected_artifact_dict = {
            stripped_uri: {
                "sha256": "ecdbcdc6bd5d2966ad1f7595874fcd6f505abd3feaa97e27bae74bcb78c38e54"
            }
        }

        artifact_dict = resolver.hash_artifacts([full_uri])
        self.assertEqual(artifact_dict, expected_artifact_dict)

    def test_colliding_lstrips(self):
        lstrip_paths = [
            f"{self._mangle_path(str(Path(__file__).parent))}/resolver/dir_resolver/",
            f"{self._mangle_path(str(Path(__file__).parent))}/resolver/colliding_dir_resolver/",
        ]

        paths = [
            str(Path(__file__).parent / "resolver" / "dir_resolver" / "subdir"),
            str(
                Path(__file__).parent
                / "resolver"
                / "colliding_dir_resolver"
                / "subdir"
            ),
        ]
        uris = [f"dir:{path}" for path in paths]

        resolver = DirectoryResolver(lstrip_paths=lstrip_paths)

        with self.assertRaises(PrefixError):
            resolver.hash_artifacts(uris)

    def test_directory_with_exclude(self):
        path = str(Path(__file__).parent / "resolver" / "dir_resolver")

        resolver = DirectoryResolver(
            exclude_patterns=["README.md"],
            normalize_line_endings=True,
        )

        uri = f"dir:{path}"
        expected_uri = self._mangle_path(uri)

        # Expected hash calculated using:
        # find . -type f | cut -c3- | LC_ALL=C sort | xargs -r sha256sum | sha256sum | cut -f1 -d' '
        expected_artifact_dict = {
            expected_uri: {
                "sha256": "c272da5259699b7bdda998e5c88dd2c5769e6c1cdbb538511f9bd46a0ad527e2"
            }
        }

        artifact_dict = resolver.hash_artifacts([uri])
        self.assertEqual(artifact_dict, expected_artifact_dict)

    def test_non_existent_directory(self):
        resolver = DirectoryResolver()
        with self.assertRaises(ValueError):
            resolver.hash_artifacts(["dir:invalid_dir"])

    def test_actual_and_non_existent_directory(self):
        path = str(Path(__file__).parent / "resolver" / "dir_resolver")

        resolver = DirectoryResolver(
            normalize_line_endings=True,
        )

        uris = ["dir:invalid_dir", f"dir:{path}"]

        with self.assertRaises(ValueError):
            resolver.hash_artifacts(uris)

    def test_actual_and_file(self):
        path = str(Path(__file__).parent / "resolver")

        resolver = DirectoryResolver(
            normalize_line_endings=True,
        )

        uris = [f"dir:{path}/README.md", f"dir:{path}/dir_resolver"]

        with self.assertRaises(ValueError):
            resolver.hash_artifacts(uris)

    def test_empty_dir(self):
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmp_dir:
            resolver = DirectoryResolver()

            uri = f"dir:{tmp_dir}"
            expected_uri = self._mangle_path(uri)
            # expected hash is sha256 hash of null input
            # find <empty-dir> -type f | cut -c3- | LC_ALL=C sort | xargs -r sha256sum | sha256sum | cut -f1 -d' '
            expected_artifact_dict = {
                expected_uri: {
                    "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                }
            }

            artifact_dict = resolver.hash_artifacts([uri])
            self.assertEqual(artifact_dict, expected_artifact_dict)


if __name__ == "__main__":
    unittest.main()
