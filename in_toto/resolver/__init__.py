# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  __init__.py

<Author>
  Alan Chung Ma <achungma@purdue.edu>

<Started>
  February 1, 2023

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Build resolver scheme dictionary and set default resolver.

"""

from in_toto.resolver.file_resolver import FileResolver
from in_toto.resolver.resolver import (
  DEFAULT_SCHEME,
  RESOLVER_FOR_URI_SCHEME,
  Resolver,
  get_scheme,
)

RESOLVER_FOR_URI_SCHEME.update(
    {
      DEFAULT_SCHEME: FileResolver,
      FileResolver.SCHEME: FileResolver,
    }
)

def set_params(**kwargs):
  """Set the parameters for the resolvers."""
  FileResolver.follow_symlink_dirs = kwargs.get("follow_symlink_dirs", False)
  FileResolver.normalize_line_endings = kwargs.get("normalize_line_endings",
                                                   False)
