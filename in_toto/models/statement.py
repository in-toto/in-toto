#!/usr/bin/env python

# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  statement.py

<Author>
  Chasen Bettinger <bettingerchasen@gmail.com>

<Started>
  Mar 25, 2023

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides a class that represents a Statement, the middle layer of an 
  attestation, binding it to a particular subject and unambiguously 
  identifying the types of the Predicate as defined in the in-toto 
  attestion spec.
"""

import attr
import securesystemslib.formats
from in_toto.models.common import Signable

STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
FILENAME_FORMAT = "{step_name}.{keyid:.8}.link"
FILENAME_FORMAT_SHORT = "{step_name}.link"
UNFINISHED_FILENAME_FORMAT = ".{step_name}.{keyid:.8}.link-unfinished"
UNFINISHED_FILENAME_FORMAT_GLOB = ".{step_name}.{pattern}.link-unfinished"


@attr.s(repr=False, init=False)
class Statement(Signable):
  """The Statement is the middle layer of the attestation, binding it to a 
  particular subject and unambiguously identifying the types of the Predicate.

  A Link object is usually contained in a generic Metablock object for signing,
  serialization and I/O capabilities.

  Attributes:
    subject: A dictionary of software artifacts that the attestation applies to. 
        Each element represents a single software artifact.

        IMPORTANT: Subject artifacts are matched purely by digest, regardless of 
        content type. If this matters to you, please comment on GitHub Issue #28
        (https://github.com/in-toto/attestation/issues/28)

        i.e.::

        {
            "name": "<NAME>",
            "digest": {
                "<ALGORITHM>": "<HEX_VALUE>"
            }
        }

    predicate_type: URI identifying the type of the Predicate.
    
    predicate: An opaque dictionary containing additional parameters of 
    the Predicate. Unset is treated the same as set-but-empty. May be 
    omitted if predicate_type fully describes the predicate.
  """
  _type = attr.ib()
  subject = attr.ib()
  predicate_type = attr.ib()
  predicate = attr.ib()
  MODEL_NAME="Statement"


  def __init__(self, **kwargs):
    super(Statement, self).__init__()

    self._type = STATEMENT_TYPE
    self.subject = kwargs.get("subject")
    self.predicate_type = kwargs.get("predicate_type")
    self.predicate = kwargs.get("predicate", {})

    self.validate()

  @property
  def type_(self):
    """ The string to indentify the in-toto metadata type."""
    # NOTE: We expose the type_ property in the API documentation instead of
    # _type to protect it against modification.
    # NOTE: Trailing underscore is used by convention (pep8) to avoid conflict
    # with Python's type keyword.
    return self._type

  @staticmethod
  def read(data):
    """Creates a Statement object from its dictionary representation.

    Arguments:
      data: A dictionary with Statement metadata fields.

    Raises:
      securesystemslib.exceptions.FormatError: Passed data is invalid.

    Returns:
      The created Statement object.

    """
    return Statement(**data)


  def _validate_type(self):
    """Private method to check that `_type` is set correctly."""
    if self._type != STATEMENT_TYPE:
      raise securesystemslib.exceptions.FormatError(
          "Invalid {}: field `_type` must be set to '{}', got: {}"
          .format(self.MODEL_NAME, STATEMENT_TYPE, self._type))


  def _validate_subject(self):
    """Private method to check that `subject` is a `list` of `HASHDICTs`."""
    if not isinstance(self.subject, list):
      raise securesystemslib.exceptions.FormatError(
          "Invalid {}: field `subject` must be of type dict, got: {}"
          .format(self.MODEL_NAME, type(self.subject)))

    for hash in self.subject:
        for subject_key in hash:
            subject_value = hash[subject_key]
            if subject_key == "name":
                if not isinstance(subject_value, str):
                    raise securesystemslib.exceptions.FormatError(
                    "Invalid {}: field `name` must be of type str, got: {}"
                    .format(self.MODEL_NAME, type(subject_value)))

                continue

            securesystemslib.formats.HASHDICT_SCHEMA.check_match(subject_value)



  def _validate_predicate_type(self):
    """Private method to check that `predicate_type` is a `str`."""
    if not isinstance(self.predicate_type, str):
      raise securesystemslib.exceptions.FormatError(
          "Invalid {}: field `predicate_type` must be of type str, got: {}"
          .format(self.MODEL_NAME, type(self.predicate_type)))

  def _validate_predicate(self):
    """Private method to check that `predicate` is a `dict`."""
    if not isinstance(self.predicate, dict):
      raise securesystemslib.exceptions.FormatError(
          "Invalid {}: field `predicate` must be of type dict, got: {}"
          .format(self.MODEL_NAME, type(self.predicate)))