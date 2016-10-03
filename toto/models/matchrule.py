import attr
import canonicaljson

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
      raise Exception("Invalid Matchrule!", data)

  def verify_rule(self, *args, **kwargs):
    raise Exception("Needs to be implemented in subclass!")

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
    assert(self.path in source_artifacts.keys())
    assert(self.step in links.keys())
    assert(self.path in links[self.step].products.keys())
    assert(artifacts[self.path] == links[self.step].products[self.path])


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
    assert(self.path in source_artifacts.keys())
    assert(self.step in links.keys())
    assert(self.path in links[self.step].materials.keys())
    assert(artifacts[self.path] == links[self.step].materials[self.path])


@attr.s(repr=False)
class Create(Matchrule): 

  path = attr.ib([])

  def __iter__(self):
    return iter(["CREATE", "{}".format(self.path)])

  def verify_rule(self, materials, products):
    """ materials and products are in the form of:
    {path : {<hashtype>: <hash>}, ...} """

    assert(self.path not in materials.keys())
    assert(self.path in products.keys())

@attr.s(repr=False)
class Delete(Matchrule): 

  path = attr.ib([])

  def __iter__(self):
    return iter(["DELETE", "{}".format(self.path)])

  def verify_rule(self, materials, products):
    """ materials and products are in the form of:
    {path : {<hashtype>: <hash>}, ...} """

    assert(self.path in materials.keys())
    assert(self.path not in products.keys())

@attr.s(repr=False)
class Modify(Matchrule): 

  path = attr.ib([])

  def __iter__(self):
    return iter(["MODIFY", "{}".format(self.path)])

  def verify_rule(self, materials, products):
    """ materials and products are in the form of:
    {path : {<hashtype>: <hash>}, ...} """

    assert(self.path in materials.keys())
    assert(self.path in products.keys())
    assert(materials[self.path] != products[self.path])
