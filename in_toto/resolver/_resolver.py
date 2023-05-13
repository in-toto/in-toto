"""Resolver interface and default file resolver implementation. """
import logging
import os
from abc import ABCMeta, abstractmethod
from itertools import combinations
from os.path import exists, isdir, isfile, join, normpath
from urllib.parse import urlunparse
import json
import http.client

from pathspec import GitIgnoreSpec
from securesystemslib.hash import digest_filename
from securesystemslib.hash import digest_fileobject

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

        digest = digest_filename(object_path, algorithm=self._HASH_ALGORITHM)

        return {self._HASH_ALGORITHM: digest.hexdigest()}

    def hash_artifacts(self, uris):
        hashes = {}

        if self._base_path:
            original_cwd = os.getcwd()
            os.chdir(self._base_path)

        for path in uris:
            # Remove scheme prefix, but preserver to re-add later
            path = self._strip_scheme_prefix(path)
            _hashes = self._hash(path)
            hashes[self._add_scheme_prefix(path)] = _hashes

        # Change back to original current working dir
        if self._base_path:
            os.chdir(original_cwd)

        return hashes


class GithubResolver(Resolver):
    """Resolver for Github entities."""

    SCHEME = "github"

    ENTITY_PR = 'pulls'
    ENTITY_COMMITS = 'commits'

    def __init__(
        self,
        org_name,
        repo_name,
        github_entity_id,
        is_github_pr=False,
        is_github_commit=False,
    ):
        if not is_github_pr and not is_github_commit:
            raise ValueError("Please choose one github entity")

        if org_name is not None:
            if not isinstance(org_name, str):
                raise ValueError("'org_name' must be string")
        if repo_name is not None:
            if not isinstance(repo_name, str):
                raise ValueError("'repo_name' must be string")
        if github_entity_id is not None:
            if not isinstance(github_entity_id, str):
                raise ValueError("'github_entity_id' must be string")

        if is_github_pr:
            github_entity = self.ENTITY_PR
        elif is_github_commit:
            github_entity = self.ENTITY_COMMITS

        path = 'repos/{}/{}/{}'.format(
            org_name+'/'+repo_name,
            github_entity,
            github_entity_id)

        self._github_entity = github_entity
        self._url = urlunparse(scheme='https',
                               netloc='api.github.com',
                               path=path)

    def _hash_review_representation(self, review):
        """
        Capture representative fields in a review and return its hash. We may want to
        be able to retrieve each status of the comment, such as CHANGES_REQUESTED and
        APPROVED. We may also want to know who reviewed the PR and approved it.
        some possible policies of reviews:
        - Reviews should be done by authorized personnel (such as the memeber of the
            organization)
        - The code should not be pushed unless it has an APPROVED state
        We can incorporate ITE-4 there for review attestations. This could be a part
        of the statement's subject.
        Args:
            Review response data from Github API calls
        Returns:
            A hash that represent a Github review
        """
        review_representation = {}
        review_representation['id'] = review['id']
        review_representation['author'] = review['user']['login']
        review_representation['author_association'] = review['author_association']
        review_representation['state'] = review['state']

        object = json.dumps(review_representation, sort_keys=True).encode()
        digest = digest_fileobject(object, algorithm=_HASH_ALGORITHM)
        hash_artifact = digest.hexdigest()

        return hash_artifact

    def _get_hashable_representation(self):
        """
        Obtain a dict that helps provide attestationns about a GitHub entity
        Returns:
            A dictionary that represent a Github enitty
        """
        conn = http.client.HTTPSConnection(self._url)
        conn.request("GET", "/", headers={
            'User-Agent': 'in-toto Reference Implementation'})
        response = conn.getresponse()
        response_data = json.loads(response.data)

        representation_object = {}
        representation_object['type'] = self._github_entity

        if self._github_entity == self.ENTITY_COMMITS:
            representation_object['commit_id'] = response_data['sha']
            representation_object['author'] = response_data['author']['login']
            representation_object['tree'] = response_data['commit']['tree']['sha']

            return representation_object

        elif self._github_entity == self.ENTITY_PR:
            representation_object['user'] = response_data['user']['login']
            representation_object['head'] = response_data['head']['label']
            representation_object['base'] = response_data['base']['label']

            representation_object['commits'] = []
            commits_url = response_data['commits_url']
            commits_conn = http.client.HTTPSConnection(str(commits_url))
            commits_conn.request("GET", "/", headers={
                'User-Agent': 'in-toto Reference Implementation'})
            commits_response = commits_conn.getresponse()
            commits_response_data = json.loads(commits_response.data)
            for commit in commits_response_data:
                representation_object['commits'].append(commit['sha'])

            representation_object['reviews'] = []
            review_url = str(self._url) + '/reviews'
            reviews_conn = http.client.HTTPSConnection(str(review_url))
            reviews_conn.request("GET", "/", headers={
                'User-Agent': 'in-toto Reference Implementation'})
            reviews_response = reviews_conn.getresponse()
            review_response_data = json.loads(reviews_response.data)
            for review in review_response_data:
                representation_object['reviews'].append(
                    self._hash_review_representation(review))

    def hash_artifacts(self):
        """
        Obtain a hash from a GitHub abstract entity
        Returns:
        A hash that represent a Github enitty
        """
        hashes = {}

        representation_object = json.dumps(self._get_hashable_representation(),
                                           sort_keys=True).encode()
        digest = digest_fileobject(representation_object,
                                   algorithm=_HASH_ALGORITHM)
        hashes[f"{self.SCHEME}:{self._url}"] = digest.hexdigest()

        return hashes
