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
import in_toto.models.common as models__common
import securesystemslib.formats

FILENAME_FORMAT = "{step_name}.{keyid:.8}.link"
UNFINISHED_FILENAME_FORMAT = ".{step_name}.{keyid:.8}.link-unfinished"

class Link(models__common.Metablock):
  """
  A link is the metadata representation of a supply chain step performed
  by a functionary.

  Links are recorded, signed and stored to a file when a functionary wraps
  a command with in_toto-run.

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
        the command that was wrapped by in_toto-run

    return_value:
        the return value of the executed command
   """

  def __init__(self, **kwargs):

    # FIXME: this is a patch that will make code migration easier.
    if 'signed' not in kwargs:
      new_kwargs = {}
      new_kwargs['signed'] = {}
      new_kwargs['signed'].update(kwargs)
      kwargs = new_kwargs

    super(Link, self).__init__(**kwargs)

  def get_signable(self):
    """ this method is used by the base class's constructor to obtain the
     appropriate signable to populate itself. """
    return _Link

  def dump(self, filename=False, key=False):
    """Write pretty printed JSON represented of self to a file with filename.
    If filename is specified, the link will be stored with that name.
    If key is specified, a filename will be created using step-name and keyid.
    If no parameter is specified (during inspection), a filename will be created
    using the link name + '.link'-suffix
    If both filename and key are provided, the key will be ignored.
    """

    if filename:
      fn = filename
    elif key:
      securesystemslib.formats.KEY_SCHEMA.check_match(key)
      fn = FILENAME_FORMAT.format(step_name=self.name, keyid=key["keyid"])
    else:
      fn = "{}.link".format(self.name)
    super(Link, self).dump(fn)

  @staticmethod
  def read_from_file(filename):
    """Static method to instantiate a new Link object from a
    canonical JSON serialized file """
    with open(filename, 'r') as fp:
      return Link.read(json.load(fp))

  @staticmethod
  def read(data):
    """Static method to instantiate a new Link from a Python dictionary """
    return Link(**data)

@attr.s(repr=False, init=False)
class _Link(models__common.Signable):
  """
  A link is the metadata representation of a supply chain step performed
  by a functionary.

  This object hold the *signable* part of a piece of link metadata. That is,
  the part from which the link's signature field will be computed.
   """
  _type = attr.ib()
  name = attr.ib()
  materials = attr.ib()
  products = attr.ib()
  byproducts = attr.ib()
  command = attr.ib()
  return_value = attr.ib()

  def __init__(self, **kwargs):
    super(_Link, self).__init__(**kwargs)

    self._type = "link"
    self.name = kwargs.get("name")
    self.materials = kwargs.get("materials", {})
    self.products = kwargs.get("products", {})
    self.byproducts = kwargs.get("byproducts", {})
    self.command = kwargs.get("command", [])
    self.return_value = kwargs.get("return_value", None)
