# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  _file_resolver.py

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

import securesystemslib.hash

from in_toto.resolver.resolver import Resolver

LOG = logging.getLogger(__name__)


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

    norm_paths = super().apply_exclude_patterns(
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
        dirpaths = super().apply_exclude_patterns(dirpaths, exclude_patterns)

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
        filepaths = super().apply_exclude_patterns(filepaths, exclude_patterns)

      for filepath in filepaths:
        normalized_filepath = filepath.replace("\\", "/")
        norm_paths.append(prepend + normalized_filepath)

    return norm_paths

  @classmethod
  def get_key_from_uri(cls, resolved_uri):
    return super().apply_left_strip(resolved_uri, cls.lstrip_paths)

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
