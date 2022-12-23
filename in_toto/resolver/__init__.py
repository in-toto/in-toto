"""
resolver contains all default artifact resolvers
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
