from common import Signable

@attr.s(repr=False)
class Link(Signable):

  _type = attr.ib("Link", init=False)
  name = attr.ib("")
  materials = attr.ib({})
  products = attr.ib({})
  byproducts = attr.ib({})
  ran_command = attr.ib("")
  return_value = attr.ib(None)

  def dump(self, filename):
    # Magic: short circuiting and string formatting
    super(Layout, self).dump(filename or "%s.link" % self._name)

  @staticmethod
  def read_from_file(filename):
    with open(filename, 'r') as fp:
      return Link.read(json.load(fp))

  @staticmethod
  def read(data)
    return Link(**link_data)
