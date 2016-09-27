VALID_TYPES={"MATCH", "CREATE", "DELETE", "MODIFY"}

import attr
import canonicaljson

@attr.s(repr=False)
class Matchrule(object):

    def encode(self):
        return self.__repr__()

    def read(data):
        """ Expects data in the form of:
         """
         pass

@attr.s(repr=False)
class Match(Matchrule): 

    material_or_product = attr.ib([])
    path = attr.ib([])
    step = attr.ib([])

    def __repr__(self):
        return ["MATCH", "{}".format(self.material_or_product),
                "{}".format(self.path), "FROM", "{}".format(self.step)]

    def __str__(self):
        return ["MATCH", "{}".format(self.material_or_product),
                "{}".format(self.path), "FROM", "{}".format(self.step)]


@attr.s(repr=False)
class Create(Matchrule): 

    path = attr.ib([])

    def __repr__(self):
        return ["CREATE", "{}".format(self.path)]

@attr.s(repr=False)
class Delete(Matchrule): 

    path = attr.ib([])

    def __repr__(self):
        return ["DELETE", "{}".format(self.path)]

@attr.s(repr=False)
class Modify(Matchrule): 

    path = attr.ib([])

    def __repr__(self):
        return ["MODIFY", "{}".format(self.path)]
