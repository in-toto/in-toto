"""Resolver interface"""

from abc import ABCMeta, abstractmethod
from pathspec import PathSpec
import re

DEFAULT_SCHEME = "default"
RESOLVER_FOR_URI_SCHEME = {}


def _get_scheme(uri):
  match = re.fullmatch(r"(\w\:[\\/])?(\w+\:)?(.+)", uri)

  if not match:
    raise ValueError(f"Artifact URI '{uri}' could not be parsed")
  groups = match.groups()
  if groups[0] or not groups[1]:
    return DEFAULT_SCHEME
  return groups[1][:-1]

def _get_resolver(uri):
  scheme = _get_scheme(uri)

  if scheme not in RESOLVER_FOR_URI_SCHEME:
    raise ValueError(
        f"Unsupported in-toto resolver scheme '{scheme}' from URI '{uri}'")

  return RESOLVER_FOR_URI_SCHEME[scheme]


class Resolver(metaclass=ABCMeta):
  """Interface for resolvers"""

  @classmethod
  def apply_exclude_patterns(cls, names, exclude_patterns):
    """Exclude matched patterns from passed names."""
    included = set(names)

    exclude_patterns = PathSpec.from_lines('gitwildmatch', exclude_patterns)

    for excluded in exclude_patterns.match_files(names):
      included.discard(excluded)

    return sorted(included)

  @classmethod
  @abstractmethod
  def resolve_uri(cls, generic_uri, exclude_patterns=None,
                  follow_symlink_dirs=False):
    """Normalize and resolve artifact URIs"""
    resolver = _get_resolver(generic_uri)
    return resolver.resolve_uri(
        generic_uri, exclude_patterns, follow_symlink_dirs)

  @classmethod
  @abstractmethod
  def get_hashable_representation(cls, resolved_uri,
                                  normalize_line_endings=False):
    """Return dictionary of hash digests"""
    resolver = _get_resolver(resolved_uri)
    return resolver.get_hashable_representation(resolved_uri,
                                                normalize_line_endings)
