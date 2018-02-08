#!/usr/bin/env python
"""
<Program Name>
  layout.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>
  Santiago Torres <santiago@nyu.edu>

<Started>
  Sep 23, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides classes related to the definition of a software supply chain.

<Classes>
  Layout:
      represents the metadata file that defines a software supply chain through
      steps and inspections

  Step:
      represents one step of the software supply chain, performed by one or many
      functionaries, who are identified by a key also stored to the layout

  Inspection:
      represents a hook that is run at verification
"""
from six import string_types

import attr
import shlex

from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

from in_toto.models.common import Signable, ValidationMixin
import in_toto.rulelib
import in_toto.exceptions
import in_toto.formats

import securesystemslib.exceptions
import securesystemslib.formats



@attr.s(repr=False, init=False)
class Layout(Signable):
  """
  A layout lists the sequence of steps of the software supply chain, and the
  functionaries authorized to perform these steps.

  The object should be contained in a generic Metablock object, which
  provides functionality for signing and signature verification, and reading
  from and writing to disk.

  <Attributes>
    _type:
        "layout"

    steps:
        a list of Step objects

    inspect:
        a list of Inspection objects

    keys:
        A dictionary of public keys used to verify the signature of link
        metadata file related to a step. Format is
        securesystemslib.formats.KEYDICT_SCHEMA

    expires:
        the expiration date of a layout

    readme:
        a human readable description of the software supply chain defined
        by the layout

  """
  _type = attr.ib()
  steps = attr.ib()
  inspect = attr.ib()
  keys = attr.ib()
  expires = attr.ib()
  readme = attr.ib()

  def __init__(self, **kwargs):
    super(Layout, self).__init__()
    self._type = "layout"
    self.steps = kwargs.get("steps", [])
    self.inspect = kwargs.get("inspect", [])
    self.keys = kwargs.get("keys", {})
    self.readme = kwargs.get("readme", "")

    # Assign a default expiration (on month) if not specified
    self.expires = kwargs.get("expires", (datetime.today() +
        relativedelta(months=1)).strftime("%Y-%m-%dT%H:%M:%SZ"))

    self.validate()

  @property
  def type_(self):
    """Getter for protected _type attribute. Trailing underscore used by
    convention (pep8) to avoid conflict with Python's type keyword. """
    return self._type

  @staticmethod
  def read(data):
    """Static method to instantiate a Layout and containing Step and Inspection
    objects from a dictionary, e.g.:
    {"steps": [<step data>, ...], "inspect": [<inspection data>, ...]} """
    steps = []

    for step_data in data.get("steps"):
      steps.append(Step.read(step_data))
    data["steps"] = steps

    inspections = []
    for inspect_data in data.get("inspect"):
      inspections.append(Inspection.read(inspect_data))
    data["inspect"] = inspections

    return Layout(**data)


  def _validate_type(self):
    """Private method to check that the type string is set to layout."""
    if self._type != "layout":
      raise securesystemslib.exceptions.FormatError(
          "Invalid _type value for layout (Should be 'layout')")

  def _validate_expires(self):
    """Private method to verify if the expiration field has the right format
    and can be parsed."""
    try:
      # We do both 'parse' and 'check_match' because the format check does not
      # detect bogus dates (e.g. Jan 35th) and parse can do more formats.
      parse(self.expires)
      securesystemslib.formats.ISO8601_DATETIME_SCHEMA.check_match(
          self.expires)
    except Exception as e:
      raise securesystemslib.exceptions.FormatError(
          "Malformed date string in layout. Exception: {}".format(e))

  def _validate_readme(self):
    """Private method to check that the readme field is a string."""
    if not isinstance(self.readme, string_types):
      raise securesystemslib.exceptions.FormatError(
          "Invalid readme '{}', value must be a string."
          .format(self.readme))

  def _validate_keys(self):
    """Private method to ensure that the keys contained are right."""
    in_toto.formats.ANY_PUBKEY_DICT_SCHEMA.check_match(self.keys)

  def _validate_steps_and_inspections(self):
    """Private method to verify that the list of steps and inspections are
    correctly formed."""

    names_seen = set()
    if type(self.steps) != list:
      raise securesystemslib.exceptions.FormatError(
          "the steps section should be a list!")

    for step in self.steps:
      if not isinstance(step, Step):
        raise securesystemslib.exceptions.FormatError(
            "The steps list should only contain steps!")

      step.validate()

      if step.name in names_seen:
        raise securesystemslib.exceptions.FormatError(
            "There is a repeated name in the steps! {}".format(step.name))
      names_seen.add(step.name)

    if type(self.inspect) != list:
      raise securesystemslib.exceptions.FormatError(
          "The inspect field should a be a list!")

    for inspection in self.inspect:
      if not isinstance(inspection, Inspection):
        raise securesystemslib.exceptions.FormatError(
            "The inspect list should only contain inspections!")

      inspection.validate()

      if inspection.name in names_seen:
        raise securesystemslib.exceptions.FormatError(
            "There is a repeated name in the steps! {}".format(inspection.name))
      names_seen.add(inspection.name)

@attr.s(repr=False, init=False)
class Step(ValidationMixin):
  """
  Represents a step of the supply chain performed by a functionary.
  A step relates to a link metadata file generated when the step was
  performed.

  <Attributes>
    name:
        a unique name used to identify the related link metadata

    expected_materials and expected_products:
        a list of artifact rules used to verify if the materials or products of
        the step (found in the according link metadata file) link correctly with
        other steps of the supply chain

    pubkeys:
        a list of keyids of the functionaries authorized to perform the step

    expected_command:
        the command expected to have performed this step

    threshold:
        the least number of functionaries expected to perform this step

  """
  _type = attr.ib()
  name = attr.ib()
  expected_materials = attr.ib()
  expected_products = attr.ib()
  pubkeys = attr.ib()
  expected_command = attr.ib()
  threshold = attr.ib()

  def __init__(self, **kwargs):
    super(Step, self).__init__()
    self._type = "step"
    self.name = kwargs.get("name")
    self.expected_materials = kwargs.get("expected_materials", [])
    self.expected_products = kwargs.get("expected_products", [])
    self.pubkeys = kwargs.get("pubkeys", [])

    # Accept expected command as string or list, if it is a string we split it
    # using shell like syntax.
    self.expected_command = kwargs.get("expected_command")
    if self.expected_command:
      if not isinstance(self.expected_command, list):
        self.expected_command = shlex.split(self.expected_command)

    else:
      self.expected_command = []

    self.threshold = kwargs.get("threshold", 1)

    self.validate()

  @staticmethod
  def read(data):
    return Step(**data)

  def _validate_type(self):
    """Private method to ensure that the type field is set to step."""
    if self._type != "step":
      raise securesystemslib.exceptions.FormatError(
          "Invalid _type value for step (Should be 'step')")

  def _validate_threshold(self):
    """Private method to check that the threshold field is set to an int."""
    if type(self.threshold) != int:
      raise securesystemslib.exceptions.FormatError(
          "Invalid threshold '{}', value must be an int."
          .format(self.threshold))

  def _validate_expected_materials(self):
    """Private method to check that material rules are correctly formed."""
    if type(self.expected_materials) != list:
      raise securesystemslib.exceptions.FormatError(
          "Material rules should be a list!")

    for rule in self.expected_materials:
      in_toto.rulelib.unpack_rule(rule)

  def _validate_expected_products(self):
    """Private method to check that product rules are correctly formed."""
    if type(self.expected_products) != list:
      raise securesystemslib.exceptions.FormatError(
          "Product rules should be a list!")

    for rule in self.expected_products:
      in_toto.rulelib.unpack_rule(rule)

  def _validate_pubkeys(self):
    """Private method to check that the pubkeys is a list of keyids."""
    if type(self.pubkeys) != list:
      raise securesystemslib.exceptions.FormatError(
          "The pubkeys field should be a list!")

    for keyid in self.pubkeys:
      securesystemslib.formats.KEYID_SCHEMA.check_match(keyid)

  def _validate_expected_command(self):
    """Private method to check that the expected_command is proper."""
    if type(self.expected_command) != list:
      raise securesystemslib.exceptions.FormatError(
          "The expected command field is malformed!")



@attr.s(repr=False, init=False)
class Inspection(ValidationMixin):
  """
  Represents an inspection which performs a command during layout verification.

  <Attributes>
    name:
        a unique name used to identify related link metadata
        link metadata for Inspections are just created and used on the fly
        and not stored to disk

    expected_materials and expected_products:
        cf. Step Attributes

    run:
        the command to execute during layout verification

  """
  _type = attr.ib()
  name = attr.ib()
  expected_materials = attr.ib()
  expected_products = attr.ib()
  run = attr.ib()

  def __init__(self, **kwargs):
    super(Inspection, self).__init__()

    self._type = "inspection"
    self.name = kwargs.get("name")
    self.expected_materials = kwargs.get("expected_materials", [])
    self.expected_products = kwargs.get("expected_products", [])

    # Accept run command as string or list, if it is a string we split it
    # using shell like syntax.
    self.run = kwargs.get("run")
    if self.run:
      if not isinstance(self.run, list):
        self.run = shlex.split(self.run)
    else:
      self.run = []

    self.validate()

  @staticmethod
  def read(data):
    return Inspection(**data)

  def _validate_type(self):
    """Private method to ensure that the type field is set to inspection."""
    if self._type != "inspection":
      raise securesystemslib.exceptions.FormatError(
          "The _type field must be set to 'inspection'!")

  def _validate_expected_materials(self):
    """Private method to check that the material rules are correct."""
    if type(self.expected_materials) != list:
      raise securesystemslib.exceptions.FormatError(
          "The material rules should be a list!")

    for rule in self.expected_materials:
      in_toto.rulelib.unpack_rule(rule)

  def _validate_expected_products(self):
    """Private method to check that the product rules are correct."""
    if type(self.expected_products) != list:
      raise securesystemslib.exceptions.FormatError(
          "The product rules should be a list!")

    for rule in self.expected_products:
      in_toto.rulelib.unpack_rule(rule)

  def _validate_run(self):
    """Private method to check that the expected command is correct."""
    if type(self.run) != list:
      raise securesystemslib.exceptions.FormatError(
          "The run field is malformed!")
