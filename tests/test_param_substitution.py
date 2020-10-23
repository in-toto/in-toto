#!/usr/bin/env python

"""
<Program Name>
  test_param_substitution.py

<Author>
  Santiago Torres-Arias <santiago@nyu.edu>

<Started>
  May 15, 2018

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test the parameter substitution functions within verifylib. These tests were
  placed in a separate module to ease refactoring in case the substitution
  layer is to be removed.

"""

import os
import shutil
import unittest

import in_toto.settings
from in_toto.models.metadata import Metablock
from in_toto.models.layout import  Layout
from in_toto.verifylib import in_toto_verify, substitute_parameters
from securesystemslib.interface import (
    import_rsa_privatekey_from_file,
    import_publickeys_from_file)

import in_toto.exceptions

from tests.common import TmpDirMixin

class Test_SubstituteArtifacts(unittest.TestCase):
  """Test parameter substitution on artifact rules. """

  def setUp(self):
    self.layout = Layout.read({
        "_type": "layout",
        "inspect": [{
          "name": "do-the-thing",
          "expected_materials": [
            ["MATCH", "{SOURCE_THING}", "WITH", "MATERIALS", "FROM",
              "{SOURCE_STEP}"]
          ],
          "expected_products": [
            ["CREATE", "{NEW_THING}"]
          ]
        }],
        "steps": [{
          "name": "artifacts",
          "expected_command": [],
          "expected_materials": [
            ["MATCH", "{SOURCE_THING}", "WITH", "MATERIALS", "FROM",
              "{SOURCE_STEP}"]
          ],
          "expected_products": [
            ["CREATE", "{NEW_THING}"]
          ]
        }]
    })

  def test_substitute(self):
    """Do a simple substitution on the expected_command field"""
    substitute_parameters(self.layout, {"SOURCE_THING": "vim",
      "SOURCE_STEP": "source_step", "NEW_THING": "new_thing"})
    self.assertEqual(self.layout.steps[0].expected_materials[0][1], "vim")
    self.assertEqual(self.layout.steps[0].expected_materials[0][5], "source_step")
    self.assertEqual(self.layout.steps[0].expected_products[0][1], "new_thing")
    self.assertEqual(self.layout.inspect[0].expected_materials[0][1], "vim")
    self.assertEqual(self.layout.inspect[0].expected_materials[0][5], "source_step")
    self.assertEqual(self.layout.inspect[0].expected_products[0][1], "new_thing")



  def test_substitute_no_var(self):
    """Raise an error if the parameter is not filled-in"""
    with self.assertRaises(KeyError):
      substitute_parameters(self.layout, {})


class Test_SubstituteRunField(unittest.TestCase):
  """Test substitution on the run field of the layout"""

  def setUp(self):
    """
    Create layout with dummy inspection
    """

    # Create layout with one inspection
    self.layout = Layout.read({
        "_type": "layout",
        "steps": [],
        "inspect": [{
          "name": "run-command",
          "run": ["{COMMAND}"],
        }]
      })

  def test_substitute(self):
    """Check that the substitution is performed on the run field."""
    substitute_parameters(self.layout, {"COMMAND": "touch"})
    self.assertEqual(self.layout.inspect[0].run[0], "touch")


  def test_inspection_fail_with_non_zero_retval(self):
    """Check that the substitution raises TypeError if the key is missing"""

    with self.assertRaises(KeyError):
      substitute_parameters(self.layout, {})


class Test_SubstituteExpectedCommand(unittest.TestCase):
  """Test verifylib.verify_command_alignment(command, expected_command)"""

  def setUp(self):
    # Create layout with one inspection
    self.layout = Layout.read({
        "_type": "layout",
        "inspect": [],
        "steps": [{
          "name": "run-command",
          "expected_command": ["{EDITOR}"],
        }]})

  def test_substitute(self):
    """Do a simple substitution on the expected_command field"""
    substitute_parameters(self.layout, {"EDITOR": "vim"})
    self.assertEqual(self.layout.steps[0].expected_command[0], "vim")


  def test_substitute_no_var(self):
    """Raise an error if the parameter is not filled-in"""

    with self.assertRaises(KeyError):
      substitute_parameters(self.layout, {"NOEDITOR": "vim"})


class Test_SubstituteOnVerify(unittest.TestCase, TmpDirMixin):
  """Test verifylib.verify_command_alignment(command, expected_command)"""

  @classmethod
  def setUpClass(self):
    # Create layout with one inspection
    self.layout = Layout.read({
        "_type": "layout",
        "inspect": [],
        "steps": [{
          "name": "run-command",
          "expected_command": ["{EDITOR}"],
        }]
      })

    # Find demo files
    demo_files = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "demo_files")

    self.set_up_test_dir()

    # Copy demo files to temp dir
    for fn in os.listdir(demo_files):
      shutil.copy(os.path.join(demo_files, fn), self.test_dir)

    # load alice's key
    self.alice = import_rsa_privatekey_from_file("alice")
    self.alice_pub_dict = import_publickeys_from_file(
        ["alice.pub"])

  @classmethod
  def tearDownClass(self):
    self.tear_down_test_dir()

  def test_substitute(self):
    """Do a simple substitution on the expected_command field"""
    signed_layout = Metablock(signed=self.layout)
    signed_layout.sign(self.alice)

    # we will catch a LinkNotFound error because we don't have (and don't need)
    # the metadata.
    with self.assertRaises(in_toto.exceptions.LinkNotFoundError):
      in_toto_verify(signed_layout, self.alice_pub_dict,
          substitution_parameters={"EDITOR":"vim"})

    self.assertEqual(self.layout.steps[0].expected_command[0], "vim")


if __name__ == "__main__":
  unittest.main()
