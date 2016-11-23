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

import toto.ssl_crypto.formats
import toto.matchrule_validators

from toto.ssl_commons.exceptions import FormatError

from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

# import validators
from . import common as models__common
from . import link as models__link
@attr.s(repr=False)
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
        a list of public keys used to verify the signature of link
        metadata file related to a step

    expires:
        the expiration date of a layout
  """

  _type = attr.ib("layout", init=False)
  steps = attr.ib([])
  inspect = attr.ib([])
  keys = attr.ib({})
  expires = attr.ib("")


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
    layout = Layout()
    tmp_steps = []
    tmp_inspect = []

    for step_data in data.get("steps"):
      tmp_steps.append(Step.read(step_data))
    for inspect_data in data.get("inspect"):
      tmp_inspect.append(Inspection.read(inspect_data))

    expires = data.get("expires")
    if not expires:
      # Set a month from now with Zulu offset as expiration date default
      expires = (datetime.today() + relativedelta(months=1)).isoformat() + 'Z'

    return Layout(steps=tmp_steps, inspect=tmp_inspect,
        keys=data.get("keys"), expires=expires,
        signatures=data.get("signatures"))

  def import_step_metadata_from_files_as_dict(self):
    """
    <Purpose>
      Iteratively loads link metadata files for each Step of the Layout
      from disk and returns a dict with Link names as keys and Link objects
      as values.

    <Arguments>
      None

    <Exceptions>
      TBA (see https://github.com/in-toto/in-toto/issues/6)

    <Side Effects>
      Calls functions to read files from disk

    <Returns>
      A dictionary with Link names as keys and Link objects as values.

    """
    step_link_dict = {}
    for step in self.steps:
      link = models__link.Link.read_from_file(step.name + '.link')
      step_link_dict[step.name] = link
    return step_link_dict

  def _validate_type(self):
    """Private method to check that the type string is set to layout."""
    if self._type != "layout":
      raise FormatError("Invalid _type value for layout (Should be 'layout')")

  def _validate_expires(self):
    """Priavte method to verify the expiration field."""
    try:
      date = parse(self.expires)
      toto.ssl_crypto.formats.ISO8601_DATETIME_SCHEMA.check_match(self.expires)
    except:
      raise FormatError("Malformed date string in layout!")

  def _validate_keys(self):
    """Private method to ensure that the keys contained are right."""
    if type(self.keys) != dict:
      raise FormatError("keys dictionary is malformed!")

    toto.ssl_crypto.formats.KEYDICT_SCHEMA.check_match(self.keys)

    for keyid, key in six.iteritems(self.keys):
      if 'private' in key and key['private'] != '':
        raise FormatError("key: {} contains a private key part!".format(keyid))

  def _validate_steps_and_inspections(self):
    """Private method to verify that the list of steps and inspections are
    correctly formed."""

    names_seen = set()
    if type(self.steps) != list:
      raise FormatError("the steps section should be a list!")

    for step in self.steps:
      if not isinstance(step, Step):
        raise FormatError("The steps list should only contain steps!")

      step.validate()

      if step.name in names_seen:
        raise FormatError("There is a repeated name in the steps! "
                          "{}".format(step.name))
      names_seen.add(step.name)

    if type(self.inspect) != list:
      raise FormatError("The inspect field should a be a list!")

    for inspection in self.inspect:
      if not isinstance(inspection, Inspection):
        raise FormatError("The inspect list should only contain inspections!")

      inspection.validate()

      if inspection.name in names_seen:
        raise FormatError("There is a repeated name in the steps! "
                          "{}".format(inspection.name))
      names_seen.add(inspection.name)

@attr.s(repr=False)
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

  """
  _type = attr.ib("step", init=False)
  name = attr.ib()
  material_matchrules = attr.ib([])
  product_matchrules = attr.ib([])
  pubkeys = attr.ib([])
  expected_command = attr.ib("")


  @staticmethod
  def read(data):
    return Step(name=data.get("name"),
        material_matchrules=data.get("material_matchrules"),
        product_matchrules=data.get("product_matchrules"),
        pubkeys=data.get("pubkeys"),
        expected_command=data.get("expected_command"))


  def _validate_type(self):
    """Private method to ensure that the type field is set to step."""
    if self._type != "step":
      raise FormatError("Invalid _type value for step (Should be 'step')")

  def _validate_threshold(self):
    """Private method to check that the threshold field is set to an int."""
    try:
      # int(self.threshold)
      # FIXME: we don't have support for threshold yet
      pass
    except:
      raise FormatError("Invalid threshold value for this step")

  def _validate_material_matchrules(self):
    """Private method to check the material matchrules are correctly formed."""
    if type(self.material_matchrules) != list:
      raise FormatError("Material matchrules should be a list!")

    for matchrule in self.material_matchrules:
      toto.matchrule_validators.check_matchrule_syntax(matchrule)

  def _validate_product_matchrules(self):
    """Private method to check the product matchrules are correctly formed."""
    if type(self.product_matchrules) != list:
      raise FormatError("Product matchrules should be a list!")

    for matchrule in self.product_matchrules:
      toto.matchrule_validators.check_matchrule_syntax(matchrule)

  def _validate_pubkeys(self):
    """Private method to check that the pubkeys is a list of keyids."""
    if type(self.pubkeys) != list:
      raise FormatError("The pubkeys field should be a list!")

    for keyid in self.pubkeys:
      toto.ssl_crypto.formats.KEYID_SCHEMA.check_match(keyid)

  def _validate_expected_command(self):
    """Private method to check that the expected_command is proper."""
    if type(self.expected_command) != str:
      raise FormatError("The expected command field is malformed!")

@attr.s(repr=False)
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

  _type = attr.ib("inspection", init=False)
  name = attr.ib()
  material_matchrules = attr.ib([])
  product_matchrules = attr.ib([])
  run = attr.ib("")


  @staticmethod
  def read(data):
    return Inspection(name=data.get("name"), run=data.get("run"),
        material_matchrules=data.get("material_matchrules"),
        product_matchrules=data.get("product_matchrules"))

  def _validate_type(self):
    """Private method to ensure that the type field is set to inspection."""
    if self._type != "inspection":
      raise FormatError("The _type field should be aset to inspection!")

  def _validate_material_matchrules(self):
    """Private method to check that the material matchrules are correct."""
    if type(self.material_matchrules) != list:
      raise FormatError("The material matchrules should be a list!")

    for matchrule in self.material_matchrules:
      toto.matchrule_validators.check_matchrule_syntax(matchrule)

  def _validate_product_matchrules(self):
    """Private method to check that the product matchrules are correct."""
    if type(self.product_matchrules) != list:
      raise FormatError("The product matchrules should be a list!")

    for matchrule in self.product_matchrules:
      toto.matchrule_validators.check_matchrule_syntax(matchrule)

  def _validate_run(self):
    """Private method to check that the expected command is correct."""
    if type(self.run) != str:
      raise FormatError("The run field is malformed!")
