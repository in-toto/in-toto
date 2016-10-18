"""
<Program Name>
  matchrule.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>
  Santiago Torres <santiago@nyu.edu>

<Started>
  Sep 23, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides classes for material and product matchrules defined in
  Step or Inspection definitions in the layout, used to verify if
  materials and products as reported by link metadata are correctly
  interconnected

<Classes>
  Matchrule:
      base class for all matchrules

  Match:
      base class for MatchProduct and MatchMaterial

  MatchProduct:
      class for matchrules of format: MATCH PRODUCT <path> FROM <step>

  Matchmaterial:
      class for matchrules of format: MATCH MATERIAL <path> FROM <step>

  Create:
      class for matchrules of format: CREATE <path>

  Delete:
      class for matchrules of format: DELETE <path>

  Modify:
      class for matchrules of format: MODIFY <path>
"""

import attr
import canonicaljson
from toto.models.common import ComparableHashDict

class RuleVerficationFailed(Exception):
  pass


@attr.s(repr=False)
class Matchrule(object):
  """
  Base class for all matchrules, provides a method to instantiate the
  different matchrules based on their list representation.

  Each subclass must implement a verify_rule method.

  <Attributes>
    source_type:
        either "material" or "product" depending on whether the rule resides
        in a material_matchrules list or product_matchrules list
  """

  source_type = attr.ib("", init=False)


  @staticmethod
  def read(data):
    # XXX LP: needs some better checking
    # e.g. move checking to validator altogether
    if len(data) == 5 and data[0] == "MATCH" and data[1] == "MATERIAL":
      return MatchMaterial(path=data[2], step=data[4])
    elif len(data) == 5 and data[0] == "MATCH" and data[1] == "PRODUCT":
      return MatchProduct(path=data[2], step=data[4])
    elif len(data) >= 2 and data[0] == "CREATE":
      return Create(path=data[1])
    elif len(data) >= 2 and data[0] == "DELETE":
      return Delete(path=data[1])
    elif len(data) >= 2 and data[0] == "MODIFY":
      return Modify(path=data[1])
    else:
      raise Exception("invalid Matchrule", data)

  def verify_rule(self):
    raise Exception("Not implemented")

@attr.s(repr=False)
class Match(Matchrule):
  """
  Base class for MatchProduct and MatchMaterial.
  Implements verify_rule which can be used by both subclasses

  <Attributes>
    path:
        the path to the material or product the be verified
        in case of MatchProduct path is a product and in case of
        MatchMaterial path is a material

    step:
        the unique name of the step to match with
  """

  path = attr.ib([])
  step = attr.ib([])


  def verify_rule(self, item_link, step_links):
    if self.source_type == "product":
      source_artifacts = item_link.products
    elif self.source_type == "material":
      source_artifacts = item_link.materials

    if isinstance(self, MatchProduct):
      target_artifacts = step_links[self.step].products
      target_type = "product"
    elif isinstance(self, MatchMaterial):
      target_artifacts = step_links[self.step].materials
      target_type = "material"
    else:
      raise Exception("Bad matchrule")

    if (self.path not in source_artifacts.keys()):
      raise RuleVerficationFailed("'%s' not in source %ss" \
          % (self.path, self.source_type))

    if (self.step not in step_links.keys()):
      raise RuleVerficationFailed("'%s' not in target links" \
          % self.step)

    if (self.path not in target_artifacts.keys()):
      raise RuleVerficationFailed("'%s' not in target %ss" \
          % (self.path, target_type))

    if (ComparableHashDict(source_artifacts[self.path]) != \
        ComparableHashDict(target_artifacts[self.path])):
      raise RuleVerficationFailed("hashes of '%s' do not match " \
          % self.path)


@attr.s(repr=False)
class MatchProduct(Match):
  """ Check if the hash of the source artifact (material or product depending
  on self.source_type) matches with the hash of the target product """
  def __iter__(self):
    return iter(["MATCH", "PRODUCT", "{}".format(self.path),
        "FROM", "{}".format(self.step)])


@attr.s(repr=False)
class MatchMaterial(Match):
  """ Check if the hash of the path (material or product depending
  on self.source_type) matches with the hash of the target material """
  def __iter__(self):
    return iter(["MATCH", "MATERIAL", "{}".format(self.path),
        "FROM", "{}".format(self.step)])


@attr.s(repr=False)
class Create(Matchrule):
  """Check if path is only in products and not in materials """
  path = attr.ib([])


  def __iter__(self):
    return iter(["CREATE", "{}".format(self.path)])


  def verify_rule(self, item_link, step_links):

    if (self.path in item_link.materials.keys()):
      raise RuleVerficationFailed("'%s' " \
          "in materials" % self.path)

    if (self.path not in item_link.products.keys()):
      raise RuleVerficationFailed("'%s' " \
          "not in products" % self.path)


@attr.s(repr=False)
class Delete(Matchrule):
  """Check if path is only in materials and not in products """
  path = attr.ib([])

  def __iter__(self):
    return iter(["DELETE", "{}".format(self.path)])

  def verify_rule(self, item_link, step_links):

    if (self.path not in item_link.materials.keys()):
      raise RuleVerficationFailed("'%s' " \
          "not in materials" % self.path)

    if (self.path in item_link.products.keys()):
      raise RuleVerficationFailed("'%s' " \
          "in products" % self.path)


@attr.s(repr=False)
class Modify(Matchrule):
  """Check if path is in products and in materials and if the related file
  hashes differ """

  path = attr.ib([])


  def __iter__(self):
    return iter(["MODIFY", "{}".format(self.path)])


  def verify_rule(self, item_link, step_links):

    if (self.path not in item_link.materials.keys()):
      raise RuleVerficationFailed("'%s' " \
          "in materials" % self.path)

    if (self.path not in item_link.products.keys()):
      raise RuleVerficationFailed("'%s' " \
          "in products" % self.path)

    if (ComparableHashDict(item_link.materials[self.path]) == \
        ComparableHashDict(item_link.products[self.path])):
      raise RuleVerficationFailed("hashes of '%s' matches" \
          % self.path)
