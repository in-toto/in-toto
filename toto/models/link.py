#!/usr/bin/env python
"""
<Program Name>
  link.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>
  Santiago Torres <santiago@nyu.edu>

<Started>
  Sep 23, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides a class for link metadata which is information gathered when a
  step of the supply chain is performed.
"""

import attr
import json
from . import common as models__common

@attr.s(repr=False)
class Link(models__common.Signable):
  """
  A link is the metadata representation of a supply chain step performed
  by a functionary.

  Links are recorded, signed and stored to a file when a functionary wraps
  a command with toto-run.

  Links also contain materials and products which are hashes of the file before
  the command was executed and after the command was executed.

  <Attributes>
    name:
        a unique name used to identify the related step in the layout
    materials and products:
        a dictionary in the format of
          { <relative file path> : {
            {<hash algorithm> : <hash of the file>}
          },... }

    byproducts:
        a dictionary in the format of
          {
            "stdout": <standard output of the executed command>
            "stderr": <standard error of the executed command>
          }

    command:
        the command that was wrapped by toto-run

    return_value:
        the return value of the executed command
   """

  _type = attr.ib("Link", init=False)
  name = attr.ib("")
  materials = attr.ib({})
  products = attr.ib({})
  byproducts = attr.ib({})
  command = attr.ib("")
  return_value = attr.ib(None)

  def dump(self, filename=False):
    """Write pretty printed JSON represented of self to a file with filename.
    If no filename is specified, a filename will be created using the link name
    + '.link'-suffix """
    # Magic: short circuiting and string formatting
    super(Link, self).dump(filename or "%s.link" % self.name)

  @staticmethod
  def read_from_file(filename):
    """Static method to instantiate a new Link object from a
    canonical JSON serialized file """
    with open(filename, 'r') as fp:
      return Link.read(json.load(fp))

  @staticmethod
  def read(data):
    """Static method to instantiate a new Link from a Python dictionary """
    # XXX LP: ugly workaround for attrs underscore strip
    # but _type is exempted from __init__ anyway
    if data.get("_type"):
      data.pop(u"_type")
    return Link(**data)
