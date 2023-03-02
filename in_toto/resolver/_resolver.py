# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  _resolver.py

<Author>
  Alan Chung Ma <achungma@purdue.edu>

<Started>
  February 1, 2023

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provide a class interface for ITE-4 generic URI resolvers.

<Classes>
  Resolver:
      interface for other in-toto resolvers to utilize

"""

from abc import ABCMeta, abstractmethod
from pathspec import PathSpec
import re

DEFAULT_SCHEME = "default"
RESOLVER_FOR_URI_SCHEME = {}


def _get_scheme(uri):
  """Obtain the resolver scheme from the generic URI.

  Arguments:
    uri: A string containing the generic URI.

  Raises:
    ValueError: Generic URI could not be parsed.

  Returns:
    The string identifying the resolver scheme.

  """
  match = re.fullmatch(r"(\w\:[\\/])?(\w+\:)?(.+)", uri)

  if not match:
    raise ValueError(f"Artifact URI '{uri}' could not be parsed")
  groups = match.groups()

  # URI scheme is set to default if URI begins with Windows drive letter or
  # does not have a resolver scheme identifier prepended.
  if groups[0] or not groups[1]:
    return DEFAULT_SCHEME

  return groups[1][:-1]

def _get_resolver(uri):
  """Obtain the resolver object from the generic URI.

  Arguments:
    uri: A string containing the generic URI.

  Raises:
    ValueError: Generic URI is not in RESOLVER_FOR_URI_SCHEME.

  Returns:
    The resolver class for the URI passed.

  """
  scheme = _get_scheme(uri)

  if scheme not in RESOLVER_FOR_URI_SCHEME:
    raise ValueError(
        f"Unsupported in-toto resolver scheme '{scheme}' from URI '{uri}'")

  return RESOLVER_FOR_URI_SCHEME[scheme]


class Resolver(metaclass=ABCMeta):
  """Interface for resolvers."""

  @classmethod
  def apply_exclude_patterns(cls, names, exclude_patterns=None):
    """Exclude matched patterns from passed names."""
    if not exclude_patterns:
      return names

    included = set(names)

    exclude_patterns = PathSpec.from_lines('gitwildmatch', exclude_patterns)

    for excluded in exclude_patterns.match_files(names):
      included.discard(excluded)

    return sorted(included)

  @classmethod
  @abstractmethod
  def resolve_uri_to_uris(cls, generic_uri, exclude_patterns=None,
                  follow_symlink_dirs=False):
    """Normalize and resolve artifact URIs."""
    resolver = _get_resolver(generic_uri)
    return resolver.resolve_uri_to_other_uris(
        generic_uri, exclude_patterns, follow_symlink_dirs)

  @classmethod
  @abstractmethod
  def get_hashable_representation(cls, resolved_uri,
                                  normalize_line_endings=False):
    """Return hashable representation of the artifact."""
    resolver = _get_resolver(resolved_uri)
    return resolver.get_hashable_representation(resolved_uri,
                                                normalize_line_endings)
