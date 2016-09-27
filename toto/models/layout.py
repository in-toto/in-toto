#!/usr/bin/env python

import json
import attr
import canonicaljson

import validators

from common import Signable
from matchrules import Matchrule

@attr.s(repr=None)
class Layout(Signable):

    _type = attr.ib(default="layout", init=False)
    steps = attr.ib([])
    validations = attr.ib([])
    keys = attr.ib([])
    expires = attr.ib()

    def __repr__(self):
        return canonicaljson.encode_pretty_printed_json(attr.asdict(self))

    def dump(self, filename='root.layout'):
        with open(filename, 'wt') as fp:
            fp.write("{}".format(self))

    @staticmethod
    def read(filename):

        with open(filename, 'r') as fp:
            layout = Layout()
            layout_data = json.load(fp)
            layout.expires = layout_data.expires

            for step_data in layout_data.steps:
                step = Step()
                step._name = step_data._name

                for data in step_data.expected_materials:
                    step.expected_materials.append(
                            Matchrule.read(data))

                for data in step_data.expected_products:
                    step.expected_products.append(
                            Matchrule.read(data))

                for data in step_data.pubkeys:
                    # create pubkey data
                    step.pubkeys.append(pubkey)

                step.expected_command.append(step_data.expected_command)

                layout.steps.append(step)


            for validation_data in layout_data.validations:
                validation = Validation()
                validation._name = validation_data._name

                for data in validation_data.expected_materials:
                    validation.expected_materials.append(
                            Matchrule.read(data))

                for data in validation_data.expected_products:
                    validation.expected_products.append(
                            Matchrule.read(data))

                validation.run = validation_data.run

                layout.validations.append(validation)


            for data in layout_data.keys:
                layout.keys.append(
                    # Create new TUF key from key
                    )

            return layout


@attr.s(repr=False)
class Step(object):

    _type = attr.ib(default="step", init=False)
    _name = attr.ib()
    expected_materials = attr.ib([])
    expected_products = attr.ib([])
    pubkeys = attr.ib([])
    expected_command = attr.ib()

    def __repr__(self):
        return canonicaljson.encode_pretty_printed_json(attr.asdict(self))

@attr.s()
class Validation(object):

    _type = attr.ib(default="validation", init=False)
    _name = attr.ib()
    expected_materials = attr.ib([])
    expected_products = attr.ib([])
    run = attr.ib()

    def __repr__(self):
        return canonicaljson.encode_pretty_printed_json(attr.asdict(self))
