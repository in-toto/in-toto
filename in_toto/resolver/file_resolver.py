# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  file_resolver.py

<Author>
  Alan Chung Ma <achungma@purdue.edu>

<Started>
  February 1, 2023

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provide resolver implementation for files.

<Classes>
  FileResolver:
      Resolver implementation for files

"""

import os
import logging
from pathspec import PathSpec

import in_toto.exceptions

from in_toto.resolver.resolver import Resolver

import securesystemslib.hash

LOG = logging.getLogger(__name__)


class FileResolver(Resolver):
  """Resolver for files"""

  SCHEME = "file"

  def __init__(self, uri):
    self.include_scheme = False
    self.hier_part = uri
    if uri.startswith(self.SCHEME):
      self.include_scheme = True
      self.hier_part = uri[len(self.SCHEME)+1:]

  def hash_artifacts(self, exclude_patterns=None, lstrip_paths=None,
      normalize_line_endings=False, hash_algorithms=None,
      follow_symlink_dirs=False, **kwargs):
    if not hash_algorithms:
      hash_algorithms = ["sha256"]

    hashed_artifacts = {}

    all_files = self._enumerate_files(self.hier_part,
        exclude_patterns=exclude_patterns,
        follow_symlink_dirs=follow_symlink_dirs)

    for path in all_files:
      digest_object = self._hash_artifact(path, hash_algorithms,
          normalize_line_endings)

      path = self._apply_left_strip(path, hashed_artifacts,
          lstrip_paths=lstrip_paths)

      hashed_artifacts[path] = digest_object
    
    if self.include_scheme:
      return {f"{self.SCHEME}:{path}": digest_object for path, digest_object \
          in hashed_artifacts.items()}

    return hashed_artifacts

  def _enumerate_files(self, generic_uri, exclude_patterns=None,
      follow_symlink_dirs=False):
    """Get all artifact names from the generic_uri.
    """
    # FIXME: not a fan of applying this against a single item in the list...
    norm_paths = self._apply_exclude_patterns(
        [os.path.normpath(generic_uri)], exclude_patterns)
    if not norm_paths:
      return norm_paths
    norm_path = norm_paths.pop()

    if os.path.isfile(norm_path):
      return [norm_path.replace('\\', '/')]

    if not os.path.isdir(norm_path):
      LOG.info("path: {} does not exist, skipping...".format(norm_path))
      return norm_paths

    for root, dirs, files in os.walk(norm_path,
        followlinks=follow_symlink_dirs):

      # Create a list of normalized dirpaths
      dirpaths = []
      for dirname in dirs:
        npath = os.path.normpath(os.path.join(root, dirname))
        dirpaths.append(npath)

      if exclude_patterns:
        dirpaths = self._apply_exclude_patterns(dirpaths, exclude_patterns)

      dirs[:] = [os.path.basename(d) for d in dirpaths]

      filepaths = []
      for filename in files:
        norm_filepath = os.path.normpath(os.path.join(root, filename))

        if os.path.isfile(norm_filepath):
          filepaths.append(norm_filepath)

        else:
          LOG.info("File '{}' appears to be a broken symlink. Skipping..."
              .format(norm_filepath))

      if exclude_patterns:
        filepaths = self._apply_exclude_patterns(filepaths, exclude_patterns)

      for filepath in filepaths:
        normalized_filepath = filepath.replace("\\", "/")
        norm_paths.append(normalized_filepath)

    return norm_paths

  def _hash_artifact(self, path, hash_algorithms, normalize_line_endings):
    digest_object = {}

    for algorithm in hash_algorithms:
      digest_object[algorithm] = securesystemslib.hash.digest_filename(path,
          algorithm=algorithm,
          normalize_line_endings=normalize_line_endings).hexdigest()

    return digest_object

  @staticmethod
  def _apply_exclude_patterns(names, exclude_patterns=None):
    """Exclude matched patterns from passed names."""
    if not exclude_patterns:
      return names

    included = set(names)

    exclude_patterns = PathSpec.from_lines('gitwildmatch', exclude_patterns)

    for excluded in exclude_patterns.match_files(names):
      included.discard(excluded)

    return sorted(included)

  @staticmethod
  def _apply_left_strip(artifact_uri, artifacts_dict, lstrip_paths=None):
    """Internal helper function to left strip dictionary keys based on
    prefixes passed by the user."""
    if lstrip_paths:
      # If a prefix is passed using the argument --lstrip-paths,
      # that prefix is left stripped from the uri passed.
      # Note: if the prefix doesn't include a trailing /, the dictionary key
      # may include an unexpected /.
      for prefix in lstrip_paths:
        if artifact_uri.startswith(prefix):
          artifact_uri = artifact_uri[len(prefix):]
          break

      if artifact_uri in artifacts_dict:
        raise in_toto.exceptions.PrefixError("Prefix selection has "
            "resulted in non unique dictionary key '{}'"
            .format(artifact_uri))

    return artifact_uri
