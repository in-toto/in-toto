#!/usr/bin/env python

VALID_TYPES={"step", "validation", "subchain"}
import json
import attr

from validators import validate_materials, validate_products

@attr.s(repr=False)
class Step(object):

    _type=attr.ib(default="Step", init=False)
    _name=attr.ib(validator=attr.validators.instance_of(str))
    materials=attr.ib([], validator=validate_materials)
    products=attr.ib([], validator=validate_products)


@attr.s()
class Link(Step):

    _type=attr.ib(default="Link", init=False)
    pubkeys=attr.ib([], attr.validators.instance_of(list))
    expected_command=attr.ib([], attr.validators.instance_of(dict))

@attr.s()
class Delegation(Step):

    _type=attr.ib(default="Delegation", init=False)
    pubkeys=attr.ib([], attr.validators.instance_of(list))

@attr.s()
class Validation(Step):

    _type=attr.ib(default="Validation", init=False)
    command=attr.ib([], attr.validators.instance_of(dict))


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

    _type=attr.ib(default="Layout", init=False)
    steps=attr.ib(validator=validate_steps)
    keys=attr.ib(validator=attr.validators.instance_of(list))
    expires=attr.ib(validator=attr.validators.instance_of(str))

    def __repr__(self):
        return json.dumps(attr.asdict(self), sort_keys=True, indent=2)

    def dump(self, filename='layout.json'):

        with open(filename, 'wt') as fp:
            fp.write("{}".format(self))
