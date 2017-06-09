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

import json
import attr
import six
import shlex

from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

from in_toto.models.link import (UNFINISHED_FILENAME_FORMAT, FILENAME_FORMAT)
import in_toto.artifact_rules
import in_toto.exceptions
import securesystemslib.exceptions
import securesystemslib.formats

# import validators
from . import common as models__common
from . import link as models__link
@attr.s(repr=False, init=False)
class Layout(models__common.Signable):
  """
  The layout specifies each of the different steps and the requirements for
  each step, as well as the public keys functionaries used to perform these
  steps.

  The layout also specifies additional steps called inspections
  that are carried out during the verification.

  Both steps and inspections can list rules that define how steps are
  interconnected by their materials and products.

  Layouts define a software supply chain and can be signed, dumped to a file,
  and instantiated from a file.

  <Attributes>
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
  """
  _type = attr.ib()
  steps = attr.ib()
  inspect = attr.ib()
  keys = attr.ib()
  expires = attr.ib()

  def __init__(self, **kwargs):
    super(Layout, self).__init__(**kwargs)
    self._type = "layout"
    self.steps = kwargs.get("steps", [])
    self.inspect = kwargs.get("inspect", [])
    self.keys = kwargs.get("keys", {})

    # Assign a default expiration (on month) if not specified
    self.expires = kwargs.get("expires", (datetime.today() +
        relativedelta(months=1)).strftime("%Y-%m-%dT%H:%M:%SZ"))

    self.validate()

  def dump(self, filename='root.layout'):
    """Write pretty printed JSON represented of self to a file with filename.
    If no filename is specified 'root.layout' is used as default """
    super(Layout, self).dump(filename)


  @staticmethod
  def read_from_file(filename='root.layout'):
    """Static method to instantiate a new Layout object from a
    canonical JSON serialized file """
    with open(filename, 'r') as fp:
      return Layout.read(json.load(fp))


  @staticmethod
  def read(data):
    """Static method to instantiate a new Layout from a Python dictionary """
    steps = []
    for step_data in data.get("steps"):
      steps.append(Step.read(step_data))
    data["steps"] = steps

    inspections = []
    for inspect_data in data.get("inspect"):
      inspections.append(Inspection.read(inspect_data))
    data["inspect"] = inspections

    return Layout(**data)

  def import_step_metadata_from_files_as_dict(self):
    """
    <Purpose>
      Iteratively loads metadata files for each Step of the Layout
      from disk, checks whether they are of type link or layout
      and loads them with the according function.
      Returns a dict with Link names as keys and a dict as values.
      The inner dict contains key_id as keys and link objects
      as values.

    <Arguments>
      None

    <Exceptions>
      TBA (see https://github.com/in-toto/in-toto/issues/6)

    <Side Effects>
      Calls functions to read files from disk

    <Returns>
      A dictionary with Link names as keys and a dict (key_id Link objects)
      as values.

    """
    step_link_dict = {}

    # Iterate over all the steps in the layout
    for step in self.steps:
      key_link_dict = {}

      for keyid in step.pubkeys:
        filename = FILENAME_FORMAT.format(step_name=step.name, keyid=keyid)

        # load the link object from the file
        try:
          with open(filename, 'r') as fp:
            link_obj = json.load(fp)

        # We try to load a link for every authorized functionary, but don't fail
        # if the file does not exist (authorized != required)
        # FIXME: Should we really pass on IOError, or just skip inexistent links
        except IOError as e:
          pass

        else:
          # Check whether the object is of type link or layout
          # and load it accordingly
          if link_obj["_type"] == "Link":
            link = models__link.Link.read(link_obj)

          elif link_obj["_type"] == "layout":
            link = Layout.read(link_obj)

          else:
            raise in_toto.exceptions.LinkNotFoundError("Invalid format".format())
          key_link_dict[keyid] = link

      # Check if the step has been performed by enough number of functionaries
      if len(key_link_dict) < step.threshold:
        raise in_toto.exceptions.LinkNotFoundError("Step not"
            " performed by enough functionaries!".format())

      step_link_dict[step.name] = key_link_dict

    return step_link_dict

  def _validate_type(self):
    """Private method to check that the type string is set to layout."""
    if self._type != "layout":
      raise securesystemslib.exceptions.FormatError(
          "Invalid _type value for layout (Should be 'layout')")

  def _validate_expires(self):
    """Private method to verify the expiration field."""
    try:
      date = parse(self.expires)
      securesystemslib.formats.ISO8601_DATETIME_SCHEMA.check_match(
          self.expires)
    except Exception as e:
      raise securesystemslib.exceptions.FormatError(
          "Malformed date string in layout. Exception: {}".format(e))

  def _validate_keys(self):
    """Private method to ensure that the keys contained are right."""
    if type(self.keys) != dict:
      raise securesystemslib.exceptions.FormatError(
          "keys dictionary is malformed!")

    securesystemslib.formats.KEYDICT_SCHEMA.check_match(self.keys)

    for keyid, key in six.iteritems(self.keys):
      securesystemslib.formats.PUBLIC_KEY_SCHEMA.check_match(key)

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
class Step(models__common.Metablock):
  """
  Represents a step of the supply chain performed by a functionary.
  A step relates to a link metadata file generated when the step was
  performed.

  <Attributes>
    name:
        a unique name used to identify the related link metadata

    material_matchrules and product_matchrules:
        a list of matchrules used to verify if the materials or products of the
        step (found in the according link metadata file) link correctly with
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
  material_matchrules = attr.ib()
  product_matchrules = attr.ib()
  pubkeys = attr.ib()
  expected_command = attr.ib()
  threshold = attr.ib()

  def __init__(self, **kwargs):
    super(Step, self).__init__()
    self._type = "step"
    self.name = kwargs.get("name")
    self.material_matchrules = kwargs.get("material_matchrules", [])
    self.product_matchrules = kwargs.get("product_matchrules", [])
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

  def _validate_material_matchrules(self):
    """Private method to check the material matchrules are correctly formed."""
    if type(self.material_matchrules) != list:
      raise securesystemslib.exceptions.FormatError(
          "Material matchrules should be a list!")

    for matchrule in self.material_matchrules:
      in_toto.artifact_rules.unpack_rule(matchrule)

  def _validate_product_matchrules(self):
    """Private method to check the product matchrules are correctly formed."""
    if type(self.product_matchrules) != list:
      raise securesystemslib.exceptions.FormatError(
          "Product matchrules should be a list!")

    for matchrule in self.product_matchrules:
      in_toto.artifact_rules.unpack_rule(matchrule)

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
class Inspection(models__common.Metablock):
  """
  Represents an inspection which performs a command during layout verification.

  <Attributes>
    name:
        a unique name used to identify related link metadata
        link metadata for Inspections are just created and used on the fly
        and not stored to disk

    material_matchrules and product_matchrules:
        cf. Step Attributes

    run:
        the command to execute during layout verification

  """
  _type = attr.ib()
  name = attr.ib()
  material_matchrules = attr.ib()
  product_matchrules = attr.ib()
  run = attr.ib()

  def __init__(self, **kwargs):
    super(Inspection, self).__init__()

    self._type = "inspection"
    self.name = kwargs.get("name")
    self.material_matchrules = kwargs.get("material_matchrules", [])
    self.product_matchrules = kwargs.get("product_matchrules", [])

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

  def _validate_material_matchrules(self):
    """Private method to check that the material matchrules are correct."""
    if type(self.material_matchrules) != list:
      raise securesystemslib.exceptions.FormatError(
          "The material matchrules should be a list!")

    for matchrule in self.material_matchrules:
      in_toto.artifact_rules.unpack_rule(matchrule)

  def _validate_product_matchrules(self):
    """Private method to check that the product matchrules are correct."""
    if type(self.product_matchrules) != list:
      raise securesystemslib.exceptions.FormatError(
          "The product matchrules should be a list!")

    for matchrule in self.product_matchrules:
      in_toto.artifact_rules.unpack_rule(matchrule)

  def _validate_run(self):
    """Private method to check that the expected command is correct."""
    if type(self.run) != list:
      raise securesystemslib.exceptions.FormatError(
          "The run field is malformed!")
