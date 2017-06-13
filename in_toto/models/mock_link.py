#!/usr/bin/env python
"""
<Program Name>
  mock_link.py

<Author>
  Shikher Verma <root@shikherverma.com>

<Started>
  June, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides a class for mock link metadata which is information gathered when a
  step of the supply chain is run as mock.
"""

import attr
import json
import in_toto.models.link as link
import securesystemslib.formats

MOCK_FILENAME_FORMAT = "{step_name}.link-mock"

@attr.s(repr=False, init=False)
class MockLink(link.Link):
  """
  A mock link is the metadata representation of a supply chain step mocked
  by a functionary.

  Mock links are recorded and stored to a file when a functionary
  wraps a command with in_toto_mock.

  Mock links also contain materials and products which are hashes of
  the file before the command was executed and after the command was executed.

  <Attributes>
    working_directory:
        the path of the directory where the command was executed
   """
  working_directory = attr.ib()

  def __init__(self, **kwargs):
    super(MockLink, self).__init__(**kwargs)

    self._type = "MockLink"
    self.working_directory = kwargs.get("working_directory", None)


  def dump(self):
    """
    Write pretty printed JSON represented of self to a file. with filename.
    A filename will be created using the link name + '.link-mock'-suffix
    """
    fn = MOCK_FILENAME_FORMAT.format(step_name=self.name)
    super(MockLink, self).dump(fn)

  @staticmethod
  def read(data):
    """Static method to instantiate a new MockLink from a Python dictionary """
    return MockLink(**data)
