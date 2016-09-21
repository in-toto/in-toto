VALID_TYPES={"MATCH", "CREATE", "DELETE", "MODIFY"}

import attr
import canonicaljson

@attr.s(repr=False)
class Matchrule(object):
    pass

    def encode(self):
        return self.__repr__()

@attr.s(repr=False)
class Match(Matchrule): 
    material_or_product=attr.ib([], attr.validators.instance_of(str))
    path=attr.ib([], attr.validators.instance_of(str))
    step=attr.ib([], attr.validators.instance_of(str))

    def __repr__(self):
        print("calling repr")
        return ["MATCH", "{}".format(self.material_or_product),
                "{}".format(self.path), "FROM", "{}".format(self.step)]

    def __str__(self):
        return ["MATCH", "{}".format(self.material_or_product),
                "{}".format(self.path), "FROM", "{}".format(self.step)]


@attr.s(repr=False)
class Create(Matchrule): 

    path=attr.ib([], attr.validators.instance_of(str))

    def __repr__(self):
        return ["CREATE", "{}".format(self.path)]

@attr.s(repr=False)
class Delete(Matchrule): 

    path=attr.ib([], attr.validators.instance_of(str))

    def __repr__(self):
        return ["DELETE", "{}".format(self.path)]

@attr.s(repr=False)
class Modify(Matchrule): 

    path=attr.ib([], attr.validators.instance_of(str))

    def __repr__(self):
        return ["MODIFY", "{}".format(self.path)]
