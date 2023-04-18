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

import securesystemslib.hash

from in_toto.resolver.resolver import Resolver, DEFAULT_SCHEME, get_scheme

LOG = logging.getLogger(__name__)


def apply_exclude_patterns(names, exclude_patterns=None):
  """Exclude matched patterns from passed names."""
  if not exclude_patterns:
    return names

  included = set(names)

  exclude_patterns = PathSpec.from_lines('gitwildmatch', exclude_patterns)

  for excluded in exclude_patterns.match_files(names):
    included.discard(excluded)

  return sorted(included)


def apply_left_strip(artifact_uri, lstrip_paths=None):
  """Internal helper function to left strip dictionary keys based on
  prefixes passed by the user."""
  scheme = get_scheme(artifact_uri)
  if scheme != DEFAULT_SCHEME:
    artifact_uri = artifact_uri[len(scheme) + 1:]
    scheme += ":"
  else:
    scheme = ""

  if lstrip_paths:
    # If a prefix is passed using the argument --lstrip-paths,
    # that prefix is left stripped from the uri passed.
    # Note: if the prefix doesn't include a trailing /, the dictionary key
    # may include an unexpected /.
    for prefix in lstrip_paths:
      if artifact_uri.startswith(prefix):
        artifact_uri = artifact_uri[len(prefix):]
        break

  return scheme + artifact_uri


class FileResolver(Resolver):
  """Resolver for files"""

  follow_symlink_dirs = False
  normalize_line_endings = False
  lstrip_paths = None
  SCHEME = "file"

  @classmethod
  def resolve_uri_to_uris(cls, generic_uri, exclude_patterns=None):
    """Get all file names from the generic_uri.
    """
    prepend = ""
    if generic_uri.startswith(cls.SCHEME + ":"):
      prepend, generic_uri = generic_uri.split(":", 1)
      prepend += ":"

    norm_paths = apply_exclude_patterns(
        [os.path.normpath(generic_uri)], exclude_patterns)
    if not norm_paths:
      return norm_paths
    norm_path = norm_paths.pop()

    if os.path.isfile(norm_path):
      return [prepend + norm_path.replace('\\', '/')]

    if not os.path.isdir(norm_path):
      LOG.info("path: {} does not exist, skipping..".format(norm_path))
      return norm_paths

    for root, dirs, files in os.walk(norm_path,
                                     followlinks=cls.follow_symlink_dirs):

      # Create a list of normalized dirpaths
      dirpaths = []
      for dirname in dirs:
        npath = os.path.normpath(os.path.join(root, dirname))
        dirpaths.append(npath)

      if exclude_patterns:
        dirpaths = apply_exclude_patterns(dirpaths, exclude_patterns)

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
        filepaths = apply_exclude_patterns(filepaths, exclude_patterns)

      for filepath in filepaths:
        normalized_filepath = filepath.replace("\\", "/")
        norm_paths.append(prepend + normalized_filepath)

    return norm_paths

  @classmethod
  def get_key_from_uri(cls, resolved_uri):
    return apply_left_strip(resolved_uri, cls.lstrip_paths)

  @classmethod
  def get_artifact_hashdict(cls, resolved_uri):
    """Takes a filename and obtain a hashable representation of the file
    contents."""
    if resolved_uri.startswith(cls.SCHEME + ":"):
      _, resolved_uri = resolved_uri.split(":", 1)

    digest_object = securesystemslib.hash.digest_filename(
      resolved_uri, 'sha256',
      normalize_line_endings=cls.normalize_line_endings)

    return {'sha256': digest_object.hexdigest()}
