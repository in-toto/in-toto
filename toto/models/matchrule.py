import attr
import canonicaljson
from toto.models.common import ComparableHashDict

class RuleVerficationFailed(Exception):
  pass

@attr.s(repr=False)
class Matchrule(object):

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
    # print "Verify rule '%s' of '%s'" % (list(self), self.__class__.__name__)

@attr.s(repr=False)
class Match(Matchrule): 

  path = attr.ib([])
  step = attr.ib([])

@attr.s(repr=False)
class MatchProduct(Match):
  
  def __iter__(self):
    return iter(["MATCH", "PRODUCT", "{}".format(self.path), 
        "FROM", "{}".format(self.step)])

  def verify_rule(self, source_artifacts, links):
    """
    source_artifacts are materials or products in the form of:
    {path : {<hashtype>: <hash>}, ...}
    links is a dictionary of link objects by identified by name
    {<link_name> : Link, ...}
    """
    if (self.path not in source_artifacts.keys()):
      raise RuleVerficationFailed("could not find path '%s' in source products" \
          % self.path)

    if (self.step not in links.keys()):
      raise RuleVerficationFailed("could not find step '%s' in links '%s'" \
          % (self.step, links.keys()))

    if (self.path not in links[self.step].products.keys()):
      raise RuleVerficationFailed("could not find path '%s' in target products" \
          % self.path)

    if (ComparableHashDict(source_artifacts[self.path]) != \
        ComparableHashDict(links[self.step].products[self.path])):
      raise RuleVerficationFailed("source artifact hash of '%s' " \
          "does not match target artifact hash" % self.path)


@attr.s(repr=False)
class MatchMaterial(Match):

  def __iter__(self):
    return iter(["MATCH", "MATERIAL", "{}".format(self.path), 
        "FROM", "{}".format(self.step)])

  def verify_rule(self, source_artifacts, links):
    """
    source_artifacts are materials or products in the form of:
    {path : {<hashtype>: <hash>}, ...}
    links is a dictionary of link objects by identified by name
    {<link_name> : Link, ...}
    """

    if (self.path not in source_artifacts.keys()):
      raise RuleVerficationFailed("could not find path '%s' in source materials" \
          % self.path)

    if (self.step not in links.keys()):
      raise RuleVerficationFailed("could not find step '%s' in links '%s'" \
          % (self.step, links.keys()))

    if (self.path not in links[self.step].materials.keys()):
      raise RuleVerficationFailed("could not find path '%s' in target materials" \
          % self.path)

    if (ComparableHashDict(source_artifacts[self.path]) != \
        ComparableHashDict(links[self.step].materials[self.path])):
      raise RuleVerficationFailed("source artifact hash of '%s' "\
          "does not match target artifact hash" % self.path)

@attr.s(repr=False)
class Create(Matchrule): 

  path = attr.ib([])

  def __iter__(self):
    return iter(["CREATE", "{}".format(self.path)])

  def verify_rule(self, materials, products):
    """ materials and products are in the form of:
    {path : {<hashtype>: <hash>}, ...} """

    if (self.path in materials.keys()):
      raise RuleVerficationFailed("newly created artifact '%s' " \
          "found in source materials" % self.path)

    if (self.path not in products.keys()):
      raise RuleVerficationFailed("newly created artifact '%s' " \
          "not found in source products" % self.path)

@attr.s(repr=False)
class Delete(Matchrule): 

  path = attr.ib([])

  def __iter__(self):
    return iter(["DELETE", "{}".format(self.path)])

  def verify_rule(self, materials, products):
    """ materials and products are in the form of:
    {path : {<hashtype>: <hash>}, ...} """

    if (self.path not in materials.keys()):
      raise RuleVerficationFailed("delete artifact '%s' " \
        "not found in source materials" % self.path)

    if (self.path in products.keys()):
      raise RuleVerficationFailed("delete artifact '%s' " \
          "found in source products" % self.path)

@attr.s(repr=False)
class Modify(Matchrule): 

  path = attr.ib([])

  def __iter__(self):
    return iter(["MODIFY", "{}".format(self.path)])

  def verify_rule(self, materials, products):
    """ materials and products are in the form of:
    {path : {<hashtype>: <hash>}, ...} """

    if (self.path not in materials.keys()):
      raise RuleVerficationFailed("modified artifact '%s' " \
          "not found in source materials" % self.path)

    if (self.path not in products.keys()):
      raise RuleVerficationFailed("delete artifact '%s' " \
        "not found in source products" % self.path)

    if (ComparableHashDict(materials[self.path]) != \
        ComparableHashDict(products[self.path])):
      raise RuleVerficationFailed("source artifact hash of '%s' " \
          "does not match target artifact hash" % self.path)
