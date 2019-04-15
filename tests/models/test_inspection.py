#!/usr/bin/env python
"""
<Program Name>
  test_inspection.py

<Author>
  Santiago Torres-Arias <santiago@nyu.edu>

<Started>
  Nov 18, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test inspection class functions.

"""

import unittest
from in_toto.models.layout import Inspection
import securesystemslib.exceptions

class TestInspectionValidator(unittest.TestCase):
  """Test verifylib.verify_delete_rule(rule, artifact_queue) """

  def setUp(self):
    """Populate a base layout that we can use."""
    self.inspection = Inspection(name="some-inspection")

  def test_wrong_type(self):
    """Test the type field within Validate()."""

    self.inspection._type = "wrong"
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.inspection._validate_type()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.inspection.validate()

    self.inspection._type = "inspection"
    self.inspection._validate_type()


  def test_wrong_run(self):
    """Test that the run validators catch malformed values."""

    self.inspection.run = -1
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.inspection._validate_run()

    with self.assertRaises(securesystemslib.exceptions.FormatError):
      self.inspection.validate()

    self.inspection.run = ["somecommand"]
    self.inspection._validate_run()
    self.inspection.validate()


  def test_set_run_from_string(self):
    """Test shelx parse command string to list. """
    inspection = Inspection()
    inspection.set_run_from_string("echo 'foo bar'")
    self.assertListEqual(inspection.run, ["echo", "foo bar"])


if __name__ == "__main__":
  unittest.main()
