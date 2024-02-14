"""Resolver interface and implementations for files, OSTree, and directory
artifacts."""

import locale
import logging
import os
from abc import ABCMeta, abstractmethod
from functools import cmp_to_key
from itertools import combinations
from os.path import exists, isdir, isfile, join, normpath

from pathspec import GitIgnoreSpec
from securesystemslib.hash import digest, digest_filename

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

        for a_, b_ in combinations(lstrip_paths, 2):
            if a_.startswith(b_) or b_.startswith(a_):
                raise PrefixError(
                    f"'{a_}' and '{b_}' triggered a left substring error"
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
        digest_obj = digest_filename(
            path,
            algorithm=_HASH_ALGORITHM,
            normalize_line_endings=self._normalize_line_endings,
        )
        return {_HASH_ALGORITHM: digest_obj.hexdigest()}

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
                name = self._mangle(path, hashes, prefix)
                hashes[name] = self._hash(path)

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

                        name = self._mangle(filepath, hashes, prefix)
                        hashes[name] = self._hash(filepath)

        # Change back to original current working dir
        if self._base_path:
            os.chdir(original_cwd)

        return hashes


class OSTreeResolver(Resolver):
    """Resolver for OSTree repositories."""

    SCHEME = "ostree"

    # defining this separately as it should be pinned to OSTree's default
    # rather than in-toto's
    _HASH_ALGORITHM = "sha256"

    def __init__(self, base_path=None):
        self._base_path = base_path

    def _strip_scheme_prefix(self, path):
        """Helper to strip OSTree resolver scheme prefix from path."""

        return path[len(self.SCHEME + ":") :]

    def _add_scheme_prefix(self, path):
        """Helper to add scheme back after recording the hash."""

        return f"{self.SCHEME}:{path}"

    def _hash(self, path):
        """Helper to hash OSTree commits."""

        ref_path = os.path.join("refs", "heads", path)

        with open(ref_path, "r") as ref:  # pylint: disable=unspecified-encoding
            ref_contents = ref.read()
        ref_contents = ref_contents.strip("\n")

        object_path = os.path.join(
            "objects", ref_contents[:2], f"{ref_contents[2:]}.commit"
        )

        digest_obj = digest_filename(
            object_path,
            algorithm=self._HASH_ALGORITHM,
        )

        return {self._HASH_ALGORITHM: digest_obj.hexdigest()}

    def hash_artifacts(self, uris):
        hashes = {}

        if self._base_path:
            original_cwd = os.getcwd()
            os.chdir(self._base_path)

        for path in uris:
            # Remove scheme prefix, but preserver to re-add later
            path = self._strip_scheme_prefix(path)
            hashes[self._add_scheme_prefix(path)] = self._hash(path)

        # Change back to original current working dir
        if self._base_path:
            os.chdir(original_cwd)

        return hashes


class DirectoryResolver(Resolver):
    """Directory resolver implementation.

    Implementation of the following shell command for some directory URI:

    find . -type f | cut -c3- | LC_ALL=C sort | xargs -r sha256sum | sha256sum |
        cut -f1 -d' '

    `exclude_patterns` are not applied on the directory paths passed to
    `hash_artifacts`, but on the files inside the directory. Similarly,
    `follow_symlink_dirs` and `normalize_line_endings` are used on
    subdirectories and files inside the directories passed to `hash_artifacts`.

    """

    SCHEME = "dir"

    def __init__(
        self,
        exclude_patterns=None,
        follow_symlink_dirs=False,
        normalize_line_endings=False,
        lstrip_paths=None,
    ):
        if not exclude_patterns:
            exclude_patterns = []

        if not lstrip_paths:
            lstrip_paths = []

        self._exclude_patterns = exclude_patterns
        self._follow_symlink_dirs = follow_symlink_dirs
        self._normalize_line_endings = normalize_line_endings
        self._lstrip_paths = lstrip_paths

    def _strip_scheme_prefix(self, path):
        """Helper to strip file resolver scheme prefix from path."""

        return path[len(self.SCHEME + ":") :]

    def _mangle(self, path, existing_paths):
        """Helper for path mangling."""

        # Normalize slashes for cross-platform metadata consistency
        path = path.replace("\\", "/")

        # Left-strip names using configured path prefixes
        for lstrip_path in self._lstrip_paths:
            if path.startswith(lstrip_path):
                path = path[len(lstrip_path) :]
                break

        # Prepend passed scheme prefix
        # We do this first because the entries in existing_paths have the scheme
        # affixed already.
        path = self.SCHEME + ":" + path

        # Fail if left-stripping above results in duplicates
        if self._lstrip_paths and path in existing_paths:
            raise PrefixError(
                "Prefix selection has resulted in non unique dictionary key "
                f"'{path}'"
            )

        return path

    def _hash(self, file_hashes):
        """Helper to correctly sort and hash every element."""

        text_repr = ""
        keys = list(file_hashes.keys())
        if keys:
            locale.setlocale(locale.LC_ALL, "C")
            keys.sort(key=cmp_to_key(locale.strcoll))

            text_repr = "\n".join(
                [f"{file_hashes[k][_HASH_ALGORITHM]}  {k}" for k in keys]
            )
            text_repr += "\n"  # trailing new line

        digest_obj = digest(_HASH_ALGORITHM)
        digest_obj.update(text_repr.encode("utf-8"))

        return {_HASH_ALGORITHM: digest_obj.hexdigest()}

    def hash_artifacts(self, uris):
        hashes = {}

        for path in uris:
            path = self._strip_scheme_prefix(path)

            if not os.path.isdir(path):
                raise ValueError(f"path '{path}' is not a directory")

            file_resolver = FileResolver(
                base_path=path,
                exclude_patterns=self._exclude_patterns,
                follow_symlink_dirs=self._follow_symlink_dirs,
                normalize_line_endings=self._normalize_line_endings,
            )

            file_hashes = file_resolver.hash_artifacts(["."])
            if not file_hashes:
                logger.info(
                    "path: %s has no files, recording empty dir...", path
                )

            name = self._mangle(path, hashes)
            hashes[name] = self._hash(file_hashes)

        return hashes
