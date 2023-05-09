"""Resolver interface and default file resolver implementation. """
import logging
import os
from abc import ABCMeta, abstractmethod
from itertools import combinations
from os.path import exists, isdir, isfile, join, normpath

from pathspec import GitIgnoreSpec
from securesystemslib.hash import digest_filename

from in_toto.exceptions import PrefixError

logger = logging.getLogger(__name__)

_HASH_ALGORITHM = "sha256"

RESOLVER_FOR_URI_SCHEME = {}


class Resolver(metaclass=ABCMeta):
    """Resolver interface and factory."""

    @classmethod
    def for_uri(cls, uri):
        """Return registered resolver instance for passed URI."""
        scheme, match, _ = uri.partition(":")

        if not match or scheme not in RESOLVER_FOR_URI_SCHEME:
            scheme = FileResolver.SCHEME

        return RESOLVER_FOR_URI_SCHEME[scheme]

    @abstractmethod
    def hash_artifacts(self, uris):
        """Return hash dictionary for passed list of artifact URIs."""
        raise NotImplementedError


class FileResolver(Resolver):
    """File resolver implementation.

    Provides a ``hash_artifacts`` method to generate hashes for passed file
    paths. The resolver is configurable via its constructor.

    """

    SCHEME = "file"

    def __init__(
        self,
        exclude_patterns=None,
        base_path=None,
        follow_symlink_dirs=False,
        normalize_line_endings=False,
        lstrip_paths=None,
    ):
        if exclude_patterns is None:
            exclude_patterns = []

        if not lstrip_paths:
            lstrip_paths = []

        if base_path is not None:
            if not isinstance(base_path, str):
                raise ValueError("'base_path' must be string")

        for name, val in [
            ("exclude_patterns", exclude_patterns),
            ("lstrip_paths", lstrip_paths),
        ]:
            if not isinstance(val, list) or not all(
                isinstance(i, str) for i in val
            ):
                raise ValueError(f"'{name}' must be list of strings")

        for _a, _b in combinations(lstrip_paths, 2):
            if _a.startswith(_b) or _b.startswith(_a):
                raise PrefixError(
                    f"'{_a}' and '{_b}' triggered a left substring error"
                )

        # Compile gitignore-style patterns
        self._exclude_filter = GitIgnoreSpec.from_lines(
            "gitwildmatch", exclude_patterns
        )
        self._base_path = base_path
        self._follow_symlink_dirs = follow_symlink_dirs
        self._normalize_line_endings = normalize_line_endings
        self._lstrip_paths = lstrip_paths

    def _exclude(self, path):
        """Helper to check, if path matches pre-compiled exclude patterns."""
        return self._exclude_filter.match_file(path)

    def _hash(self, path):
        """Helper to generate hash dictionary for path."""
        digest = digest_filename(
            path,
            algorithm=_HASH_ALGORITHM,
            normalize_line_endings=self._normalize_line_endings,
        )
        return {_HASH_ALGORITHM: digest.hexdigest()}

    def _mangle(self, path, existing_paths, scheme_prefix):
        """Helper for path mangling."""

        # Normalize slashes for cross-platform metadata consistency
        path = path.replace("\\", "/")

        # Left-strip names using configured path prefixes
        for lstrip_path in self._lstrip_paths:
            if path.startswith(lstrip_path):
                path = path[len(lstrip_path) :]
                break

        # Fail if left-stripping above results in duplicates
        if self._lstrip_paths and path in existing_paths:
            raise PrefixError(
                "Prefix selection has resulted in non unique dictionary key "
                f"'{path}'"
            )

        # Prepend passed scheme prefix
        path = scheme_prefix + path

        return path

    def _strip_scheme_prefix(self, path):
        """Helper to strip file resolver scheme prefix from path."""

        prefix = self.SCHEME + ":"
        if path.startswith(prefix):
            path = path[len(prefix) :]
        else:
            prefix = ""

        return path, prefix

    def hash_artifacts(self, uris):
        hashes = {}

        if self._base_path:
            original_cwd = os.getcwd()
            os.chdir(self._base_path)

        for path in uris:
            # Remove scheme prefix, but preserver to re-add later (see _mangle)
            path, prefix = self._strip_scheme_prefix(path)

            # Normalize URI before filtering and returning them
            # FIXME: Is this expected behavior? Does this make exclude patterns
            # with slashes platform-dependent? Check how 'gitwildmatch' treats
            # dots and slashes!
            path = normpath(path)

            if self._exclude(path):
                continue

            if not exists(path):
                logger.info("path: %s does not exist, skipping..", path)
                continue

            if isfile(path):
                _name = self._mangle(path, hashes, prefix)
                _hashes = self._hash(path)
                hashes[_name] = _hashes

            if isdir(path):
                for base, dirs, names in os.walk(
                    path, followlinks=self._follow_symlink_dirs
                ):
                    # Filter directories to avoid unnecessary recursion below
                    # NOTE: Normalize to filter on directory paths without
                    # their dot-slash prefix, if path was dot.
                    dirs[:] = [
                        dirname
                        for dirname in dirs
                        if not self._exclude(normpath(join(base, dirname)))
                    ]

                    for filename in names:
                        # NOTE: Normalize to filter on and return file paths
                        # without their dot-slash prefix, if path was dot.
                        filepath = normpath(join(base, filename))

                        if self._exclude(filepath):
                            continue

                        if not isfile(filepath):
                            logger.info(
                                "File '%s' appears to be a broken symlink. "
                                "Skipping...",
                                filepath,
                            )
                            continue

                        _name = self._mangle(filepath, hashes, prefix)
                        _hashes = self._hash(filepath)
                        hashes[_name] = _hashes

        # Change back to original current working dir
        if self._base_path:
            os.chdir(original_cwd)

        return hashes
