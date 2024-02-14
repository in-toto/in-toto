"""Test cases for resolver.py."""

from pathlib import Path
from unittest import TestCase, main

from in_toto.resolver import RESOLVER_FOR_URI_SCHEME, FileResolver, Resolver
from tests.common import TmpDirMixin


class TestResolver(TestCase):
    """Test default and custom resolver registration and dispatch."""

    def test_register(self):
        self.assertFalse(RESOLVER_FOR_URI_SCHEME)  # assert empty

        class Default(Resolver):
            def hash_artifacts(self, uris):
                pass

        class Custom(Resolver):
            def hash_artifacts(self, uris):
                pass

        # uris with: default scheme, non-registered scheme, no scheme
        uris = ["file:path/to/file", "C:\\path\\to\\file", "path/to/file"]

        # Raise if no scheme is registered (default must be registered too)
        for uri in uris:
            with self.assertRaises(KeyError, msg=f"uri={uri}"):
                Resolver.for_uri(uri)

        RESOLVER_FOR_URI_SCHEME["file"] = Default()
        RESOLVER_FOR_URI_SCHEME["custom"] = Custom()

        # Once registered, all uris w/o (registered) scheme resolve to default.
        for uri in uris:
            self.assertIsInstance(Resolver.for_uri(uri), Default, f"uri={uri}")

        self.assertIsInstance(Resolver.for_uri("custom:path"), Custom)
        self.assertIsInstance(Resolver.for_uri("custom"), Default)  # no scheme

        RESOLVER_FOR_URI_SCHEME.clear()


class TestFileResolver(TmpDirMixin, TestCase):
    """Test hash_artifacts with and without scheme.

    See 'test_runlib' for comprehensive tests of file hash recording.
    """

    @classmethod
    def setUpClass(cls):
        cls.set_up_test_dir()  # tear_down_test_dir is called implicitly
        Path("foo").touch()
        Path("bar").mkdir()
        Path("bar/baz").touch()
        Path("bar/foo").touch()

    def test_hash_artifacts_scheme_no_scheme(self):
        """Assert that hashes are the same with and without scheme."""
        resolver = FileResolver()
        uris = {"foo", "file:foo"}
        result = resolver.hash_artifacts(uris)
        self.assertEqual(result.keys(), uris)
        # pylint: disable=no-value-for-parameter
        self.assertEqual(*result.values())

    def test_hash_artifacts_kwags(self):
        """Assert return values for hash_artifacts with different config."""
        # Test data: kwargs, uris, expected return value (dict keys)
        test_data = [
            ({"base_path": "bar"}, {"file:baz"}, {"file:baz"}),
            ({"lstrip_paths": ["bar/"]}, {"file:bar/baz"}, {"file:baz"}),
            (
                {"exclude_patterns": ["file*", "baz"]},
                {"file:foo", "file:bar"},
                {"file:foo", "file:bar/foo"},
            ),
        ]

        for kwargs, uris, expected_keys in test_data:
            resolver = FileResolver(**kwargs)
            result = resolver.hash_artifacts(uris)
            self.assertEqual(result.keys(), expected_keys)


if __name__ == "__main__":
    main()
