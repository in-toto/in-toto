#!/usr/bin/env python

import json
import attr

# import validators
from . import common as models__common
from . import matchrule as models__matchrule

@attr.s(repr=False)
class Layout(models__common.Signable):

  _type = attr.ib("layout", init=False)
  steps = attr.ib([])
  inspect = attr.ib([])
  keys = attr.ib([])
  expires = attr.ib("")

  def dump(self, filename='root.layout'):
    super(Layout, self).dump(filename)

  @staticmethod
  def read_from_file(filename):
    with open(filename, 'r') as fp: 
      return Layout.read(json.load(fp))

  @staticmethod
  def read(data):
    layout = Layout()
    tmp_steps = []
    tmp_inspect = []

    for step_data in data.get("steps"):
      tmp_steps.append(Step.read(step_data))
    for inspect_data in data.get("inspect"):
      tmp_inspect.append(Inspection.read(inspect_data))

    return Layout(steps=tmp_steps, inspect=tmp_inspect,
        keys=data.get("keys"), expires=data.get("expires"),
        signatures=data.get("signatures"))

@attr.s(repr=False)
class Step(models__common.Metablock):

  _type = attr.ib("step", init=False)
  name = attr.ib()
  material_matchrules = attr.ib([])
  product_matchrules = attr.ib([])
  pubkeys = attr.ib([])
  expected_command = attr.ib("")

  @staticmethod
  def read(data):
    tmp_material_matchrules = []
    tmp_product_matchrules = []

    # We just store the list representation of Matchrules because it makes
    # serialization/deserialization easier.
    for matchrule in data.get("material_matchrules"):
      tmp_material_matchrules.append(
          list(models__matchrule.Matchrule.read(matchrule)))
    for matchrule in data.get("product_matchrules"):
      tmp_product_matchrules.append(
          list(models__matchrule.Matchrule.read(matchrule)))

    return Step(name=data.get("name"),
        material_matchrules=tmp_material_matchrules,
        product_matchrules=tmp_product_matchrules,
        pubkeys=data.get("pubkeys"),
        expected_command=data.get("expected_command"))

@attr.s(repr=False)
class Inspection(models__common.Metablock):

  _type = attr.ib("inspection", init=False)
  name = attr.ib()
  material_matchrules = attr.ib([])
  product_matchrules = attr.ib([])
  run = attr.ib("")

  @staticmethod
  def read(data):
    tmp_material_matchrules = []
    tmp_product_matchrules = []

    # We just store the list representation of Matchrules because it makes
    # serialization/deserialization easier.
    for matchrule in data.get("material_matchrules"):
      tmp_material_matchrules.append(
          list(models__matchrule.Matchrule.read(matchrule)))
    for matchrule in data.get("product_matchrules"):
      tmp_product_matchrules.append(
          list(models__matchrule.Matchrule.read(matchrule)))

    return Inspection(name=data.get("name"), run=data.get("run"),
        material_matchrules=tmp_material_matchrules,
        product_matchrules=tmp_product_matchrules)
