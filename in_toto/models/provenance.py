#!/usr/bin/env python

# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  provenance.py

<Author>
  Furkan Türkal <furkan.turkal@trendyol.com>

<Started>
  Aug 3, 2021

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides a class for provenance metadata which is information gathered when a
  step of the supply chain is performed.
"""

import attr
import securesystemslib.formats
from in_toto.models.common import Signable
from in_toto.verifylib import _get_attribute

FILENAME_FORMAT = "{step_name}.{keyid:.8}.provenance"
FILENAME_FORMAT_SHORT = "{step_name}.provenance"
UNFINISHED_FILENAME_FORMAT = ".{step_name}.{keyid:.8}.provenance-unfinished"
UNFINISHED_FILENAME_FORMAT_GLOB = ".{step_name}.{pattern}.provenance-unfinished"


@attr.s(repr=False, init=False)
class Provenance(Signable):
  """Evidence for a performed step or inspection of the supply chain.

  SPEC: https://github.com/in-toto/attestation/blob/main/spec/predicates/provenance.md

  Provenance is a claim that some entity (builder) produced one or more
  software artifacts (Statement's subject) by executing some recipe,
  using some other artifacts as input (materials).

  Attributes:
    builder: Identifies the entity that executed the recipe, which is
        trusted to have correctly performed the operation and populated this
        provenance.

        {
          "id": "<URI>"
        }

    recipe: Identifies the configuration used for the build. When combined with
        materials, this SHOULD fully describe the build, such that re-running
        this recipe results in bit-for-bit identical output (if the build is
        reproducible).

        {
          "type": "<URI>",
          "definedInMaterial": /* integer */,
          "entryPoint": "<STRING>",
          "arguments": { /* object */ },
          "environment": { /* object */ }
        }

    metadata: Other properties of the build.

            {
              "buildInvocationId": "<STRING>",
              "buildStartedOn": "<TIMESTAMP>",
              "buildFinishedOn": "<TIMESTAMP>",
              "completeness": {
                "arguments": true/false,
                "environment": true/false,
                "materials": true/false
              },
              "reproducible": true/false
            }

    materials: The collection of artifacts that influenced the build
        including sources, dependencies, build tools, base images,
        and so on.

            {
              "uri": "<URI>",
              "digest": { /* DigestSet */ }
            }

  """
  _type = attr.ib()
  builder = attr.ib()
  recipe = attr.ib()
  metadata = attr.ib()
  materials = attr.ib()

  def __init__(self, **kwargs):
    super(Provenance, self).__init__()

    self._type = "provenance"
    self.builder = kwargs.get("builder", {"id": "foo://bar"})
    self.recipe = kwargs.get("recipe", {"type": "foo://bar", "definedInMaterial": 0, "entryPoint": "", "arguments": {}, "environment": {}})
    self.metadata = kwargs.get("metadata", {"buildInvocationId": "", "buildStartedOn": 1628017067, "buildFinishedOn": 1628017089, "reproducible": False, "completeness": {"arguments": False, "environment": False, "materials": False}})
    self.materials = kwargs.get("materials", [{"uri": "foo://bar", "digest": {"md5": "8f961ea23d77b9b8c01a12b2818e1055"}}])

    self.validate()

  @property
  def type_(self):
    """The string "provenance" to identify the in-toto metadata type."""
    # NOTE: We expose the type_ property in the API documentation instead of
    # _type to protect it against modification.
    # NOTE: Trailing underscore is used by convention (pep8) to avoid conflict
    # with Python's type keyword.
    return self._type

  @staticmethod
  def read(data):
    """Creates a Provenance object from its dictionary representation.

    Arguments:
      data: A dictionary with provenance metadata fields.

    Raises:
      securesystemslib.exceptions.FormatError: Passed data is invalid.

    Returns:
      The created Provenance object.

    """
    return Provenance(**data)

  def _validate_type(self):
    """Private method to check that `_type` is set to "Provenance"."""
    if self._type != "provenance":
      raise securesystemslib.exceptions.FormatError(
          "Invalid Link: field `_type` must be set to 'provenance', got: {}"
          .format(self._type))

    securesystemslib.formats.URL_SCHEMA.check_match(self._type)

  def _validate_builder(self):
    """Private method to check that `builder` is a `dict`."""
    if not isinstance(self.builder, dict):
      raise securesystemslib.exceptions.FormatError(
          "Invalid Link: field `builder` must be of type dict, got: {}"
          .format(type(self.builder)))

    securesystemslib.formats.URL_SCHEMA.check_match(self.builder["id"])

  def _validate_recipe(self):
    """Private method to check that `builder` is a `dict`."""
    if not isinstance(self.recipe, dict):
      raise securesystemslib.exceptions.FormatError(
          "Invalid Link: field `recipe` must be of type dict, got: {}"
          .format(type(self.recipe)))

    if self.recipe is not None:
      assert _get_attribute(self.recipe, 'type')

      securesystemslib.formats.URL_SCHEMA.check_match(self.recipe['type'])
      # TODO: securesystemslib.formats.ANY_NUMBER_SCHEMA.check_match(self.recipe.type)

      if _get_attribute(self.recipe, 'entryPoint'):
        securesystemslib.formats.ANY_STRING_SCHEMA.check_match(self.recipe['entryPoint'])

      if _get_attribute(self.recipe, 'arguments'):
        if not isinstance(self.recipe['arguments'], dict):
          raise securesystemslib.exceptions.FormatError(
            "Invalid Link: field `recipe.arguments` must be of type dict, got: {}"
              .format(type(self.recipe['arguments'])))

      if _get_attribute(self.recipe, 'environment'):
        if not isinstance(self.recipe['environment'], dict):
          raise securesystemslib.exceptions.FormatError(
            "Invalid Link: field `recipe.environment` must be of type dict, got: {}"
              .format(type(self.recipe['environment'])))

  def _validate_metadata(self):
    """Private method to check that `builder` is a `dict`."""
    if not isinstance(self.metadata, dict):
      raise securesystemslib.exceptions.FormatError(
        "Invalid Link: field `metadata` must be of type dict, got: {}"
          .format(type(self.metadata)))

    if _get_attribute(self.metadata, 'buildInvocationId'):
      securesystemslib.formats.ANY_STRING_SCHEMA.check_match(self.metadata['buildInvocationId'])
    if _get_attribute(self.metadata, 'buildStartedOn'):
      securesystemslib.formats.UNIX_TIMESTAMP_SCHEMA.check_match(self.metadata['buildStartedOn'])
    if _get_attribute(self.metadata, 'buildFinishedOn'):
      securesystemslib.formats.UNIX_TIMESTAMP_SCHEMA.check_match(self.metadata['buildFinishedOn'])
    if _get_attribute(self.metadata, 'reproducible'):
      securesystemslib.formats.BOOLEAN_SCHEMA.check_match(self.metadata['reproducible'])

    if _get_attribute(self.metadata, 'completeness'):
      """Check that `completeness` is a `dict`."""
      if not isinstance(self.metadata['completeness'], dict):
        raise securesystemslib.exceptions.FormatError(
          "Invalid Link: field `metadata.completeness` must be of type dict, got: {}"
            .format(type(self.metadata.completeness)))

      if _get_attribute(self.metadata['completeness'], 'arguments'):
        securesystemslib.formats.BOOLEAN_SCHEMA.check_match(self.metadata['completeness']['arguments'])
      if _get_attribute(self.metadata['completeness'], 'environment'):
        securesystemslib.formats.BOOLEAN_SCHEMA.check_match(self.metadata['completeness']['environment'])
      if _get_attribute(self.metadata['completeness'], 'materials'):
        securesystemslib.formats.BOOLEAN_SCHEMA.check_match(self.metadata['completeness']['materials'])

  def _validate_materials(self):
    """Private method to check that `command` is a `list`."""
    if not isinstance(self.materials, list):
      raise securesystemslib.exceptions.FormatError(
        "Invalid Link: field `materials` must be of type dict, got: {}"
          .format(type(self.materials)))

    for material in list(self.materials):
      if _get_attribute(material, 'uri'):
        securesystemslib.formats.URL_SCHEMA.check_match(material['uri'])
      if _get_attribute(material, 'digest'):
        securesystemslib.formats.HASHDICT_SCHEMA.check_match(material['digest'])
