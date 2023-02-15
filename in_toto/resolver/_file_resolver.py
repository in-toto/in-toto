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

from securesystemslib.storage import FilesystemBackend

from in_toto.resolver._resolver import Resolver

LOG = logging.getLogger(__name__)


class FileResolver(Resolver):
  """Resolver for files"""

  SCHEME = "file"

  @classmethod
  def resolve_uri(cls, generic_uri, exclude_patterns=None,
                  follow_symlink_dirs=False):
    """Get all file names from the generic_uri.
    """
    if generic_uri.startswith(cls.SCHEME + ":"):
      generic_uri = generic_uri[len(cls.SCHEME)+1:]

    norm_paths = super().apply_exclude_patterns(
        [os.path.normpath(generic_uri)], exclude_patterns)
    if not norm_paths:
      return norm_paths
    norm_path = norm_paths.pop()

    if os.path.isfile(norm_path):
      return [norm_path.replace('\\', '/')]

    if not os.path.isdir(norm_path):
      LOG.info("path: {} does not exist, skipping..".format(norm_path))
      return norm_paths

    for root, dirs, files in os.walk(norm_path,
        followlinks=follow_symlink_dirs):

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
        norm_paths.append(normalized_filepath)

    return norm_paths

  @classmethod
  def get_hashable_representation(cls, resolved_uri,
                                  normalize_line_endings=False):
    """Takes a filename and obtain a hashable representation of the file
    contents."""

    data = b""

    with FilesystemBackend().get(resolved_uri) as file_object:
      data = file_object.read()

      if normalize_line_endings:
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")

    return data
