#!/usr/bin/env python
"""
<Program Name>
  test_common.py

<Author>
  Santiago Torres-Arias <santiago@nyu.edu>

<Started>
  Sept 26, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test the Signable and ValidationMixin class functions.

"""

import unittest
import json
from in_toto.models.common import Signable

class TestSignable(unittest.TestCase):
  """ Verifies Signable class. """

  def test_load_repr_string_as_json(self):
    """Test load string returned by `Signable.repr` as JSON  """
    json.loads(repr(Signable()))

if __name__ == "__main__":
  unittest.main()
