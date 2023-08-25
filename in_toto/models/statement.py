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
  attestation spec.
"""

import attr

import in_toto_attestation.v1.statement_pb2 as statementpb
import in_toto_attestation.v1.resource_descriptor_pb2 as rdpb
from google.protobuf.json_format import MessageToDict
from in_toto.models.common import Signable

STATEMENT_TYPE = "https://in-toto.io/Statement/v1"


# NOTE: 08/24/23 - This function is an intentional
# hack to alter JSON after it has been serialized
# to a JSON from a Protobuf. Every object that is
# a member of a part of a class that is a child of
# the Signable class must be able to be represented
# via canonical JSON. Floats are not allowed in
# canonical JSON, but there is a function within the
# Securesystemslib library that is able to protect
# against this. However, the code to resolve this
# particular issue is not yet implemented and until
# it is, this function specifically protects against
# the case where the return-value of a Link's
# byproducts changes from 0 to 0.0 and consequently
# prevents the entire class from resolving to a
# correct `signable_bytes` property.
def _enforce_canonical_json(obj):
    for k in obj:
        val = obj[k]
        if isinstance(val, dict):
            _enforce_canonical_json(val)
        if isinstance(val, float):
            nv = int(val)
            obj[k] = nv

    return obj


@attr.s(repr=False, init=False)
class Statement(Signable):
    """https://github.com/in-toto/attestation/blob/main/spec/v1.0/statement.md"""

    _type = attr.ib()
    predicateType = attr.ib()
    predicate = attr.ib()
    subject = attr.ib()
    MODEL_NAME = "Statement"

    def __init__(self, **kwargs):
        super(Statement, self).__init__()

        statement = statementpb.Statement()
        statement.type = STATEMENT_TYPE
        # camelCase here because of protobuf requirements
        statement.predicateType = kwargs.get("predicateType")
        statement.predicate.update(kwargs.get("predicate", {}))
        subjects = kwargs.get("subject", [])

        for subject in subjects:
            if not isinstance(subject, rdpb.ResourceDescriptor):
                subject = rdpb.ResourceDescriptor(**subject)

            statement.subject.append(subject)

        # NOTE: We need to serialize the protobuf into JSON
        # so that we can sign the contents downstream
        serialized_statement = MessageToDict(statement)
        serialized_statement = _enforce_canonical_json(serialized_statement)

        # This is to assign attributes onto the class
        # itself so the properties are directly accessible.
        for k, v in serialized_statement.items():
            setattr(self, k, v)

        if hasattr(self, "subject") == False:
            self.subject = []

    @property
    def type_(self):
        """The string to indentify the in-toto metadata type."""
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

    # def _validate_type(self):
    #     """Private method to check that `_type` is set correctly."""
    #     if self._type != STATEMENT_TYPE:
    #         raise securesystemslib.exceptions.FormatError(
    #             "Invalid {}: field `_type` must be set to '{}', got: {}"
    #             .format(self.MODEL_NAME, STATEMENT_TYPE, self._type))

    # def _validate_statement(self):
    #     """Private method to check that `subject` is a `list` of `HASHDICTs`."""
    #     if not isinstance(self.statement, statementpb.Statement):
    #         raise securesystemslib.exceptions.FormatError(
    #             "Invalid {}: field `statement` must be of type statement protobuf, got: {}"
    #             .format(self.MODEL_NAME, type(self.statement)))

    # def _validate_subject(self):
    #     """Private method to check that `subject` is a `list` of `HASHDICTs`."""
    #     if not isinstance(self.statement.subject, list):
    #         raise securesystemslib.exceptions.FormatError(
    #             "Invalid {}: field `subject` must be of type dict, got: {}"
    #             .format(self.MODEL_NAME, type(self.statement.subject)))

    #     for hash in self.statement.subject:
    #         for subject_key in hash:
    #             subject_value = hash[subject_key]
    #             if subject_key == "name":
    #                 if not isinstance(subject_value, str):
    #                     raise securesystemslib.exceptions.FormatError(
    #                         "Invalid {}: field `name` must be of type str, got: {}"
    #                         .format(self.MODEL_NAME, type(subject_value)))

    #                 continue

    #             securesystemslib.formats.HASHDICT_SCHEMA.check_match(
    #                 subject_value)

    # def _validate_predicate_type(self):
    #     """Private method to check that `predicate_type` is a `str`."""
    #     if not isinstance(self.statement.predicate_type, str):
    #         raise securesystemslib.exceptions.FormatError(
    #             "Invalid {}: field `predicate_type` must be of type str, got: {}"
    #             .format(self.MODEL_NAME, type(self.predicate_type)))

    # def _validate_predicate(self):
    #     """Private method to check that `predicate` is a `dict`."""
    #     if not isinstance(self.statement.predicate, dict):
    #         raise securesystemslib.exceptions.FormatError(
    #             "Invalid {}: field `predicate` must be of type dict, got: {}"
    #             .format(self.MODEL_NAME, type(self.statement.predicate)))
