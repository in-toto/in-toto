#!/usr/bin/env python

VALID_TYPES={"step", "validation"}
import json
import attr
import canonicaljson

from validators import validate_materials, validate_products
from common import Metablock

@attr.s(repr=False)
class Step(Metablock):

    _type=attr.ib(default="step", init=False)
    materials=attr.ib([], validator=validate_materials)
    products=attr.ib([], validator=validate_products)
    pubkeys=attr.ib([], attr.validators.instance_of(list))
    expected_command=attr.ib([], attr.validators.instance_of(dict))


@attr.s()
class Validation(Metablock):

    _type=attr.ib(default="validation", init=False)
    materials=attr.ib([], validator=validate_materials)
    products=attr.ib([], validator=validate_products)
    run=attr.ib([], attr.validators.instance_of(str))

def validate_steps(self, Attribute, steps):

    self.steps_seen = set()
    if not isinstance(steps, list):
        raise TypeError("steps expects a list of Step objects!")

    for step in steps:

        if step._name in self.steps_seen:
            raise TypeError("steps can't have a repeated name!")

        if not isinstance(step, Step):
            raise TypeError("steps can only contain Step instances!")

        self.steps_seen.add(step._name)   

@attr.s(repr=None)
class Layout(object):

    _type=attr.ib(default="layout", init=False)
    steps=attr.ib(validator=validate_steps)
    keys=attr.ib(validator=attr.validators.instance_of(list))
    expires=attr.ib(validator=attr.validators.instance_of(str))

    def __repr__(self):
        return canonicaljson.encode_pretty_printed_json(attr.asdict(self))

    def dump(self, filename='layout.json'):

        with open(filename, 'wt') as fp:
            fp.write("{}".format(self))



