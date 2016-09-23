#!/usr/bin/env python

import json
import attr
import canonicaljson

@attr.s(repr=False)
class Metablock(object):

    def __repr__(self):
        return canonicaljson.encode_pretty_printed_json(attr.asdict(self))

    _name=attr.ib(validator=attr.validators.instance_of(str))
