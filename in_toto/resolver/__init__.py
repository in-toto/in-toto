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

from in_toto.resolver._file_resolver import FileResolver
from in_toto.resolver._resolver import (
  DEFAULT_SCHEME,
  RESOLVER_FOR_URI_SCHEME,
  Resolver,
)

RESOLVER_FOR_URI_SCHEME.update(
    {
      DEFAULT_SCHEME: FileResolver,
      FileResolver.SCHEME: FileResolver,
    }
)
