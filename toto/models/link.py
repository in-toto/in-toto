from common import Signable

@attr.s(repr=False)
class Link(SignedFile):

    _type = attr.ib(default="Link", init=False)
    _name = attr.ib()
    materials = attr.ib([])
    products = attr.ib([])
    ran_command = attr.ib()
    return_value = attr.ib()


    def dump(self, filename):
        with open(filename, 'wt') as fp:
            fp.write("{}".format(self))

    @staticmethod
    def read(filename):
        with open(filename, 'r') as fp:

            link = Link()
            link_data = json.load(fp)

            link._name = link_data._name
            link.command = link_data.command

            for filepath, filehash in link_data.materials.iteritems():
                link.materials[filepath] = filehash

            for filepath, filehash in link_data.products.iteritems():
                link.products[filepath] = filehash

            for key, val in link_data.byproducts.iteritems():
                link.byproducts[key] = val

            return link
