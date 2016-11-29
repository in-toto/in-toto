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

@attr.s(repr=False)
class Match(Matchrule): 

  path = attr.ib([])
  step = attr.ib([])

@attr.s(repr=False)
class MatchProduct(Match):
  
  def __iter__(self):
    return iter(["MATCH", "PRODUCT", "{}".format(self.path), 
        "FROM", "{}".format(self.step)])


@attr.s(repr=False)
class MatchMaterial(Match):

  def __iter__(self):
    return iter(["MATCH", "MATERIAL", "{}".format(self.path), 
        "FROM", "{}".format(self.step)])

@attr.s(repr=False)
class Create(Matchrule): 

  path = attr.ib([])

  def __iter__(self):
    return iter(["CREATE", "{}".format(self.path)])

@attr.s(repr=False)
class Delete(Matchrule): 

  path = attr.ib([])

  def __iter__(self):
    return iter(["DELETE", "{}".format(self.path)])

@attr.s(repr=False)
class Modify(Matchrule): 

  path = attr.ib([])

  def __iter__(self):
    return iter(["MODIFY", "{}".format(self.path)])
