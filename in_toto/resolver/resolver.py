# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  resolver.py

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

DEFAULT_SCHEME = ""
RESOLVER_FOR_URI_SCHEME = {}

class Resolver(metaclass=ABCMeta):
  """Interface for resolvers."""

  @classmethod
  def for_uri(cls, uri):
    scheme, match, _ = uri.partition(":")
    if not match or scheme not in RESOLVER_FOR_URI_SCHEME:
      scheme = DEFAULT_SCHEME
    return RESOLVER_FOR_URI_SCHEME[scheme](uri)

  @abstractmethod
  def hash_artifacts(self, **kwargs):
    """Return hashes of the artifacts. """
    raise NotImplementedError
