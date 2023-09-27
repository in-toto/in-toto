# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  common.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>
  Santiago Torres <santiago@nyu.edu>

<Started>
  Sep 23, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides base classes for various classes in the model.

"""

import inspect
import json

import attr
import securesystemslib.formats


class ValidationMixin:
    """The validation mixin provides a self-inspecting method, validate, to
    allow in-toto's objects to check that they are proper."""

    def validate(self):
        """Validates attributes of the instance.

        Raises:
          securesystemslib.formats.FormatError: An attribute value is invalid.

        """
        for method in inspect.getmembers(self, predicate=inspect.ismethod):
            if method[0].startswith("_validate_"):
                method[1]()


@attr.s(repr=False, init=False)
class Signable(ValidationMixin):
    """Objects with base class Signable are to be included in a Metablock class
    to be signed (hence the name). They provide a `signable_bytes` property
    used to create deterministic signatures."""

    def __repr__(self):
        """Returns an indented JSON string of the metadata object."""
        return json.dumps(
            attr.asdict(self), indent=1, separators=(",", ": "), sort_keys=True
        )

    @property
    def signable_bytes(self):
        """The UTF-8 encoded canonical JSON byte representation of the dictionary
        representation of the instance."""
        return securesystemslib.formats.encode_canonical(
            attr.asdict(self)
        ).encode("UTF-8")


class BeautifyMixin:
    """The beautify mixin provides a method to represent in-toto's metadata
    object into a friendly and readable form as a string."""

    def _beautify(self, data, level=0, width=4):
        """Helper function for beautify method. This function recursively
        unpacks data in given dictionary object into a string.

        Arguments:
          data: dictionary object containing metadata key-value pairs. Keys
              are metadata field names and values are the metadata values.
          level: integer representing level of nesting that determines
              indentation.
          width: integer representing the size of single indentation.

        Returns:
          A string that presents in-toto metadata in a readable form.
        """
        indent = " " * (level * width)
        s = []

        if isinstance(data, (str, int)):
            return str(data)

        if isinstance(data, list):
            s.append("\n")
            for item in data:
                s.append(f"{indent}{self._beautify(item, level)}\n")

        elif isinstance(data, dict):  # Includes OrderedDict - dict is superset
            s.append("\n")
            for key, val in data.items():
                if not val:
                    continue

                s.append(f"{indent}{key}: ")
                s.append(f"{self._beautify(val, level=level+1)}\n")

        return "".join(s).rstrip()

    def beautify(self, order=None):
        """Translates in-toto metadata object into audit-friendly string
        representation.

        Arguments:
          order: list of string specifying fields to be included and the
              order in which they are to be arranged.

        Returns:
          A string that presents in-toto metadata in a readable form.
        """
        data = self.get_beautify_dict(order)
        return self._beautify(data).strip()


class MetadataFields:
    """Common in-toto metadata fields"""

    TYPE = "Type"
    EXPIRATION = "Expiration"
    KEYS = "Keys"
    STEPS = "Steps"
    INSPECTIONS = "Inspections"
    EXPECTED_COMMAND = "Expected Command"
    EXPECTED_MATERIALS = "Expected Materials"
    EXPECTED_PRODUCTS = "Expected Products"
    PUBKEYS = "Pubkeys"
    THRESHOLD = "Threshold"
    RUN = "Run"
