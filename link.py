import json
import attr

@attr.s(repr=False)
class Link(object):

    _type=attr.ib(default="Link", init=False)
    _name=attr.ib(validator=attr.validators.instance_of(str))
    materials=attr.ib([], validator=attr.validators.instance_of(list))
    products=attr.ib([], validator=attr.validators.instance_of(list))
    command_ran=attr.ib([], validator=attr.validators.instance_of(str))
    return_value=attr.ib([], validator=attr.validators.instance_of(int))
