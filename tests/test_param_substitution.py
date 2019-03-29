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
import copy
import tempfile
import unittest
import glob
import common

from mock import patch
from datetime import datetime
from dateutil.relativedelta import relativedelta

import in_toto.settings
from in_toto.models.metadata import Metablock
from in_toto.models.link import Link, FILENAME_FORMAT
from in_toto.models.layout import (Step, Inspection, Layout,
    SUBLAYOUT_LINK_DIR_FORMAT)
from in_toto.verifylib import (verify_delete_rule, verify_create_rule,
    verify_modify_rule, verify_allow_rule, verify_disallow_rule,
    verify_match_rule, verify_item_rules, verify_all_item_rules,
    verify_command_alignment, run_all_inspections, in_toto_verify,
    verify_sublayouts, get_summary_link, _raise_on_bad_retval,
    load_links_for_layout, verify_link_signature_thresholds,
    verify_threshold_constraints, substitute_parameters)
from in_toto.exceptions import (RuleVerificationError,
    SignatureVerificationError, LayoutExpiredError, BadReturnValueError,
    ThresholdVerificationError)
from in_toto.util import import_rsa_key_from_file, import_public_keys_from_files_as_dict
import in_toto.gpg.functions

import securesystemslib.exceptions
import in_toto.exceptions


class Test_SubstituteArtifacts(common.TestCaseLib):
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
    self.assertEquals(self.layout.steps[0].expected_materials[0][1], "vim")
    self.assertEquals(self.layout.steps[0].expected_materials[0][5], "source_step")
    self.assertEquals(self.layout.steps[0].expected_products[0][1], "new_thing")
    self.assertEquals(self.layout.inspect[0].expected_materials[0][1], "vim")
    self.assertEquals(self.layout.inspect[0].expected_materials[0][5], "source_step")
    self.assertEquals(self.layout.inspect[0].expected_products[0][1], "new_thing")



  def test_substitute_no_var(self):
    """Raise an error if the parameter is not filled-in"""
    with self.assertRaises(KeyError):
      substitute_parameters(self.layout, {})


class Test_SubstituteRunField(common.TestCaseLib):
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
    self.assertEquals(self.layout.inspect[0].run[0], "touch")


  def test_inspection_fail_with_non_zero_retval(self):
    """Check that the substitution raises TypeError if the key is missing"""

    with self.assertRaises(KeyError):
      substitute_parameters(self.layout, {})


class Test_SubstituteExpectedCommand(common.TestCaseLib):
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
    self.assertEquals(self.layout.steps[0].expected_command[0], "vim")


  def test_substitute_no_var(self):
    """Raise an error if the parameter is not filled-in"""

    with self.assertRaises(KeyError):
      substitute_parameters(self.layout, {"NOEDITOR": "vim"})


class Test_SubstituteOnVerify(common.TestCaseLib):
  """Test verifylib.verify_command_alignment(command, expected_command)"""

  extra_settings = "demo"

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

    super(Test_SubstituteOnVerify, self).setUpClass()

    # load alice's key
    self.alice = import_rsa_key_from_file("alice")
    self.alice_pub_dict = import_public_keys_from_files_as_dict(
      ["alice.pub"])

  def test_substitute(self):
    """Do a simple substitution on the expected_command field"""
    signed_layout = Metablock(signed=self.layout)
    signed_layout.sign(self.alice)

    # we will catch a LinkNotFound error because we don't have (and don't need)
    # the metadata.
    with self.assertRaises(in_toto.exceptions.LinkNotFoundError):
      in_toto_verify(signed_layout, self.alice_pub_dict,
          substitution_parameters={"EDITOR":"vim"})

    self.assertEquals(self.layout.steps[0].expected_command[0], "vim")


if __name__ == "__main__":
  unittest.main()
