#!/usr/bin/env python

# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  test_statement.py

<Author>
  Chasen Bettinger <bettingerchasen@gmail.com>

<Started>
  Mar 25, 2023

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test statement class functions.

"""

import copy
import unittest
from in_toto.models.statement import Statement
from securesystemslib.exceptions import FormatError

_correct_subject = [
    {
        "name": "ok", 
        "digest": {
            "sha256": "abc"
        }
    }
]

_correct_predicate_type = "http://in-toto.io/attestation/human-review/vcs/v0.1"

_correct_predicate = {
    "result": "approved",
    "reviewLink": "https://github.com/in-toto/in-toto/pull/503#pullrequestreview-1341209941",
    "timestamp": "2023-03-15T11:05:00Z",
    "reviewer": "https://github.com/lukpueh"
}

def _get_statement():
    subject = _correct_subject

    predicate_type = _correct_predicate_type

    return Statement(
        subject=subject,
        predicate_type=predicate_type
    )

class TestStatementValidator(unittest.TestCase):
  """Test statement format validators """

  def test_validate_type(self):
    """Test `_type` field. Must be "https://in-toto.io/Statement/v1" """
    test = copy.deepcopy(_get_statement())

    # Good type
    test._type = "https://in-toto.io/Statement/v1"
    test.validate()

    # Bad type
    test._type = "bad statement"
    with self.assertRaises(FormatError):
      test.validate()

  def test_validate_subject(self):
    """Test `subject` field. Must be a `dict`"""
    test = copy.deepcopy(_get_statement())

    # Good type
    test.subject = _correct_subject
    test.validate()

    # Missing `name` property
    incorrect_subject = copy.deepcopy(_correct_subject)
    incorrect_subject[0]["name"] = None
    test.subject = incorrect_subject
    with self.assertRaises(FormatError):
      test.validate()

    # `name` property is not a string
    incorrect_subject = copy.deepcopy(_correct_subject)
    incorrect_subject[0]["name"] = False
    test.subject = incorrect_subject
    with self.assertRaises(FormatError):
      test.validate()

    # Missing `digest` dictionary
    incorrect_subject = copy.deepcopy(_correct_subject)
    incorrect_subject[0]["digest"] = None
    test.subject = incorrect_subject
    with self.assertRaises(FormatError):
      test.validate()

    # `digest` property is not a dict
    incorrect_subject = copy.deepcopy(_correct_subject)
    incorrect_subject[0]["digest"] = False
    test.subject = incorrect_subject
    with self.assertRaises(FormatError):
      test.validate()

  def test_validate_predicate_type(self):
    """Test `predicate_type` field. Must be a `str`"""
    test = copy.deepcopy(_get_statement())

    # Good type
    test.predicate_type = _correct_predicate_type
    test.validate()

    # Missing `predicate_type` property
    test.predicate_type = None
    with self.assertRaises(FormatError):
      test.validate()

    # `predicate_type` property is not a string
    test.predicate_type = False
    with self.assertRaises(FormatError):
      test.validate()

  def test_validate_predicate(self):
    """Test `predicate` field. Must be a `dict` if supplied"""
    test = copy.deepcopy(_get_statement())

    # Good type
    test.predicate = _correct_predicate
    test.validate()

    # Missing `predicate_type` property
    # is ok, should default to empty dictionary
    test = copy.deepcopy(_get_statement())
    test.validate()

    # `predicate_type` property is not a string
    test.predicate_type = False
    with self.assertRaises(FormatError):
      test.validate()

if __name__ == "__main__":
  unittest.main()