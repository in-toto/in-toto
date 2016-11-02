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
from datetime import datetime
from dateutil.relativedelta import relativedelta

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
  keys = attr.ib([])
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
