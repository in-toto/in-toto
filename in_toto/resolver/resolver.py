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
import re

import securesystemslib.formats
import securesystemslib.hash

DEFAULT_SCHEME = "default"
RESOLVER_FOR_URI_SCHEME = {}


def get_scheme(uri):
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
  scheme = get_scheme(uri)

  if scheme not in RESOLVER_FOR_URI_SCHEME:
    raise ValueError(
        f"Unsupported in-toto resolver scheme '{scheme}' from URI '{uri}'")

  return RESOLVER_FOR_URI_SCHEME[scheme]


class Resolver(metaclass=ABCMeta):
  """Interface for resolvers."""

  @classmethod
  @abstractmethod
  def resolve_uri_to_uris(cls, generic_uri, exclude_patterns=None):
    """Normalize and resolve artifact URIs."""
    resolver = _get_resolver(generic_uri)
    return resolver.resolve_uri_to_uris(generic_uri, exclude_patterns)

  @classmethod
  @abstractmethod
  def get_key_from_uri(cls, resolved_uri):
    """Get dictionary key for the output from the resolved URI."""

  @classmethod
  @abstractmethod
  def get_artifact_hashdict(cls, resolved_uri):
    """Get hashdict of the artifact that will pass the schema check."""

  @classmethod
  def hash_artifact(cls, resolved_uri):
    """Return hashes of the artifact."""
    resolver = _get_resolver(resolved_uri)

    hash_dict = resolver.get_artifact_hashdict(resolved_uri)
    securesystemslib.formats.HASHDICT_SCHEMA.check_match(hash_dict)

    return resolver.get_key_from_uri(resolved_uri), hash_dict