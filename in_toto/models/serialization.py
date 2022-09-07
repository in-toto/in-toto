# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  serialization.py

<Started>
  Sep 6, 2022

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides serialization/ deserialization classes
  for various classes in the model.

"""

from typing import Union

from securesystemslib.exceptions import DeserializationError
from securesystemslib.serialization import JSONDeserializer

from in_toto.exceptions import InvalidMetadata
from in_toto.models.layout import Layout
from in_toto.models.link import Link
from in_toto.models.metadata import Envelope, Metablock, ENVELOPE_PAYLOAD_TYPE


class PayloadDeserializer(JSONDeserializer):
  """Deserialize JSON bytes into Link or Layout."""

  def deserialize(self, raw_data: bytes) -> Union[Link, Layout]:
    """Deserialize JSON bytes into Link or Layout object."""

    data = super().deserialize(raw_data)
    _type = data.get("_type")
    if _type == "link":
      return Link.read(data)
    if _type == "layout":
      return Layout.read(data)

    raise DeserializationError(
      f"Invalid payload type {_type}, must be `link` or `layout`"
    )


class AnyMetadataDeserializer(JSONDeserializer):
  """Deserialize bytes into Metablock / DSSE Envelope."""

  def deserialize(self, raw_data: bytes) -> Union["Envelope", "Metablock"]:
    """Deserialize JSON bytes into Metablock or Envelope as per ITE-5. """

    data = super().deserialize(raw_data)

    if "payload" in data:
      if data.get("payloadType") == ENVELOPE_PAYLOAD_TYPE:
        return Envelope.from_dict(data)

    elif "signed" in data:
      return Metablock.from_dict(data)

    raise InvalidMetadata
