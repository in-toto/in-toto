import attr
from . import common as models__common

@attr.s(repr=False)
class Link(models__common.Signable):

  _type = attr.ib("Link", init=False)
  name = attr.ib("")
  materials = attr.ib({})
  products = attr.ib({})
  byproducts = attr.ib({})
  ran_command = attr.ib("")
  return_value = attr.ib(None)

  def dump(self, filename=False):
    # Magic: short circuiting and string formatting
    super(Link, self).dump(filename or "%s.link" % self.name)

  @staticmethod
  def read_from_file(filename):
    with open(filename, 'r') as fp:
      return Link.read(json.load(fp))

  @staticmethod
  def read(data):
    return Link(**data)
