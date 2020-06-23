#!/usr/bin/env python
"""
<Program Name>
  link.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>
  Santiago Torres <santiago@nyu.edu>

<Started>
  Sep 23, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides a class for link metadata which is information gathered when a
  step of the supply chain is performed.
"""

import attr
import securesystemslib.formats
from in_toto.models.common import Signable


FILENAME_FORMAT = "{step_name}.{keyid:.8}.link"
FILENAME_FORMAT_SHORT = "{step_name}.link"
UNFINISHED_FILENAME_FORMAT = ".{step_name}.{keyid:.8}.link-unfinished"
UNFINISHED_FILENAME_FORMAT_GLOB = ".{step_name}.{pattern}.link-unfinished"


@attr.s(repr=False, init=False)
class Link(Signable):
  """Evidence for a performed step or inspection of the supply chain.

  A Link object is usually contained in a generic Metablock object for signing,
  serialization and I/O capabilities.

  Attributes:
    name: A unique name used to identify the related step or inspection in an
        in-toto layout.

    command: A list of command and command arguments that report how the
        corresponding step is performed.

    materials: A dictionary of the artifacts *used* by the step, i.e::

            {
              "<material path>": {
                "<hash algorithm name>": "<hash digest of material>",
                ...
              },
              ...
            }

    products: A dictionary of the artifacts *produced* by the step, i.e::

            {
              "<product path>": {
                "<hash algorithm name>": "<hash digest of product>",
                ...
              },
              ...
            }

    byproducts: An opaque dictionary that lists byproducts of the link command
        execution. It should have at least the following entries
        "stdout" (str), "stderr" (str) and "return-value" (int).

    environment: An opaque dictionary that lists information about the
        execution environment of the link command. eg.::

            {
              "variables": "<list of env var KEY=value pairs>",
              "filesystem": "<filesystem info>",
              "workdir": "<CWD when executing link command>"
            }

  """
  _type = attr.ib()
  name = attr.ib()
  materials = attr.ib()
  products = attr.ib()
  byproducts = attr.ib()
  command = attr.ib()
  environment = attr.ib()


  def __init__(self, **kwargs):
    super(Link, self).__init__()

    self._type = "link"
    self.name = kwargs.get("name")
    self.materials = kwargs.get("materials", {})
    self.products = kwargs.get("products", {})
    self.byproducts = kwargs.get("byproducts", {})
    self.command = kwargs.get("command", [])
    self.environment = kwargs.get("environment", {})

    self.validate()

  @property
  def type_(self):
    """The string "link" to indentify the in-toto metadata type."""
    # NOTE: We expose the type_ property in the API documentation instead of
    # _type to protect it against modification.
    # NOTE: Trailing underscore is used by convention (pep8) to avoid conflict
    # with Python's type keyword.
    return self._type

  @staticmethod
  def read(data):
    """Creates a Link object from its dictionary representation.

    Arguments:
      data: A dictionary with link metadata fields.

    Raises:
      securesystemslib.exceptions.FormatError: Passed data is invalid.

    Returns:
      The created Link object.

    """
    return Link(**data)


  def _validate_type(self):
    """Private method to check that `_type` is set to "link"."""
    if self._type != "link":
      raise securesystemslib.exceptions.FormatError(
          "Invalid Link: field `_type` must be set to 'link', got: {}"
          .format(self._type))


  def _validate_materials(self):
    """Private method to check that `materials` is a `dict` of `HASHDICTs`."""
    if not isinstance(self.materials, dict):
      raise securesystemslib.exceptions.FormatError(
          "Invalid Link: field `materials` must be of type dict, got: {}"
          .format(type(self.materials)))

    for material in list(self.materials.values()):
      securesystemslib.formats.HASHDICT_SCHEMA.check_match(material)


  def _validate_products(self):
    """Private method to check that `products` is a `dict` of `HASHDICTs`."""
    if not isinstance(self.products, dict):
      raise securesystemslib.exceptions.FormatError(
          "Invalid Link: field `products` must be of type dict, got: {}"
          .format(type(self.products)))

    for product in list(self.products.values()):
      securesystemslib.formats.HASHDICT_SCHEMA.check_match(product)


  def _validate_byproducts(self):
    """Private method to check that `byproducts` is a `dict`."""
    if not isinstance(self.byproducts, dict):
      raise securesystemslib.exceptions.FormatError(
          "Invalid Link: field `byproducts` must be of type dict, got: {}"
          .format(type(self.byproducts)))


  def _validate_command(self):
    """Private method to check that `command` is a `list`."""
    if not isinstance(self.command, list):
      raise securesystemslib.exceptions.FormatError(
          "Invalid Link: field `command` must be of type list, got: {}"
          .format(type(self.command)))


  def _validate_environment(self):
    """Private method to check that `environment` is a `dict`. """
    if not isinstance(self.environment, dict):
      raise securesystemslib.exceptions.FormatError(
          "Invalid Link: field `environment` must be of type dict, got: {}"
          .format(type(self.environment)))
