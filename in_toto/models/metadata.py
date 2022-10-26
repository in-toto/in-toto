# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  metadata.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>
  Santiago Torres <santiago@nyu.edu>

<Started>
  Oct 23, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides a container class `Metablock` for signed metadata and
  functions for signing, signature verification, de-serialization and
  serialization from and to JSON.

"""

import attr
import copy
import json
from typing import Optional, List, Union

import securesystemslib.keys
import securesystemslib.formats
import securesystemslib.exceptions
import securesystemslib.gpg.functions
from securesystemslib.exceptions import SignatureVerificationError
from securesystemslib.key import Key
from securesystemslib.metadata import Envelope as SSlibEnvelope
from securesystemslib.signer import GPGSignature, Signature, Signer
from securesystemslib.serialization import (BaseDeserializer, BaseSerializer,
    JSONSerializer, SerializationMixin)

from in_toto.models.common import Signable, ValidationMixin
from in_toto.models.link import Link
from in_toto.models.layout import Layout


ENVELOPE_PAYLOAD_TYPE = "application/vnd.in-toto+json"


# pylint: disable=import-outside-toplevel
class AnyMetadata(SerializationMixin):
  """A Metadata abstraction between DSSE Envelope and Metablock."""

  @staticmethod
  def _default_deserializer() -> BaseDeserializer:
    from in_toto.models.serialization import AnyMetadataDeserializer
    return AnyMetadataDeserializer()

  @staticmethod
  def _default_serializer() -> BaseSerializer:
    return JSONSerializer()


class Envelope(AnyMetadata, SSlibEnvelope):
  """DSSE Envelope for in-toto payloads."""

  @classmethod
  def from_signable(cls, signable: Signable) -> "Envelope":
    """Creates DSSE envelope with signable bytes as payload."""

    return cls(
      payload=signable.to_bytes(),
      payload_type=ENVELOPE_PAYLOAD_TYPE,
      signatures=[]
    )

  def get_payload(self, deserializer: Optional[BaseDeserializer] = None
  ) -> Union[Link, Layout]:
    """Parse DSSE payload into Link or Layout object.

      Arguments:
          deserializer: ``securesystemslib.serialization.BaseDeserializer``
              implementation to use. Default is ``PayloadDeserializer``.

      Raises:
          securesystemslib.exceptions.DeserializationError: The payload
              cannot be deserialized.

      Returns:
          Link or Layout.
    """

    if deserializer is None:
      from in_toto.models.serialization import PayloadDeserializer
      deserializer = PayloadDeserializer()

    return super().get_payload(deserializer)


@attr.s(repr=False, init=False)
class Metablock(ValidationMixin, AnyMetadata):
  """A container for signed in-toto metadata.

  Provides methods for metadata JSON (de-)serialization, reading from and
  writing to disk, creating and verifying signatures, and self-validation.

  Attributes:
    signed: A subclass of Signable which has the actual metadata payload,
        usually a Link or Layout object.
    signatures: A list of signatures over the canonical JSON representation
        of the value of the signed attribute.
    compact_json: A boolean indicating if the dump method should write a
        compact JSON string representation of the metadata.

  """
  signatures = attr.ib()
  signed = attr.ib()


  def __init__(self, **kwargs):
    self.signatures = kwargs.get("signatures", [])
    self.signed = kwargs.get("signed")
    self.compact_json = kwargs.get("compact_json", False)

    self.validate()


  def __repr__(self):
    """Returns the JSON string representation. """
    indent = None if self.compact_json else 1
    separators = (',', ':') if self.compact_json else (',', ': ')

    return json.dumps(
        {
          "signatures": self.signatures,
          "signed": attr.asdict(self.signed)
        },
        indent=indent,
        separators=separators,
        sort_keys=True
      )


  @classmethod
  def from_dict(cls, data: dict) -> "Metablock":
    """Creates a Metablock object from its JSON/dict representation."""

    signatures = data.get("signatures", [])
    signed_data = data.get("signed", {})
    signed_type = signed_data.get("_type")

    if signed_type == "link":
      signed = Link.read(signed_data)

    elif signed_type == "layout":
      signed = Layout.read(signed_data)

    else:
      raise securesystemslib.exceptions.FormatError("Invalid Metadata format")

    return cls(signatures=signatures, signed=signed)


  def to_dict(self) -> dict:
    """Returns the JSON-serializable dictionary representation of self."""

    return {
      "signatures": self.signatures,
      "signed": attr.asdict(self.signed)
    }


  def dump(self, path):
    """Writes the JSON string representation of the instance to disk.

    Arguments:
      path: The path to write the file to.

    Raises:
      IOError: File cannot be written.

    """
    with open(path, "wb") as fp:
      fp.write("{}".format(self).encode("utf-8"))


  @staticmethod
  def load(path):
    """Loads the JSON string representation of in-toto metadata from disk.

    Arguments:
      path: The path to read the file from.

    Raises:
      IOError: The file cannot be read.
      securesystemslib.exceptions.FormatError: Metadata format is invalid.

    Returns:
      A Metablock object whose signable attribute is either a Link or a Layout
      object.

    """
    with open(path, "r", encoding="utf8") as fp:
      data = json.load(fp)

    return Metablock.from_dict(data)



  @property
  def type_(self):
    """A shortcut to the `type_` attribute of the object on the signable
    attribute (should be one of "link" or "layout"). """
    # NOTE: Trailing underscore is used by convention (pep8) to avoid conflict
    # with Python's type keyword.
    return self.signed.type_


  def create_sig(self, signer: Signer):
    """Creates signature over signable with Signer and adds it to signatures.

    Uses the UTF-8 encoded canonical JSON byte representation of the signable
    attribute to create signatures deterministically.

    Arguments:
      signer: A "Signer" class instance to create signature.

    Raises:
      securesystemslib.exceptions.FormatError: Key argument is malformed.
      securesystemslib.exceptions.CryptoError, \
              securesystemslib.exceptions.UnsupportedAlgorithmError:
          Signing errors.

    Returns:
      The signature. A securesystemslib.signer.Signature type.

    """
    signature = signer.sign(self.signed.signable_bytes)

    self.signatures.append(signature.to_dict())

    return signature

  def sign(self, key):
    """Creates signature over signable with key and adds it to signatures.

    Uses the UTF-8 encoded canonical JSON byte representation of the signable
    attribute to create signatures deterministically.

    Attributes:
      key: A signing key. The format is securesystemslib.formats.KEY_SCHEMA.

    Raises:
      securesystemslib.exceptions.FormatError: Key argument is malformed.
      securesystemslib.exceptions.CryptoError, \
              securesystemslib.exceptions.UnsupportedAlgorithmError:
          Signing errors.

    Returns:
      The signature. Format is securesystemslib.formats.SIGNATURE_SCHEMA.

    """
    securesystemslib.formats.KEY_SCHEMA.check_match(key)

    signature = securesystemslib.keys.create_signature(key,
        self.signed.signable_bytes)

    self.signatures.append(signature)

    return signature

  def sign_gpg(self, gpg_keyid=None, gpg_home=None):
    """Creates signature over signable with gpg and adds it to signatures.

    Uses the UTF-8 encoded canonical JSON byte representation of the signable
    attribute to create signatures deterministically.

    Arguments:
      gpg_keyid (optional): A keyid used to identify a local gpg signing key.
          If omitted the default signing key is used.

      gpg_home (optional): A path to the gpg home directory. If not set the
          default gpg home directory is used.

    Raises:
      ValueError, OSError, securesystemslib.gpg.exceptions.CommandError, \
            securesystemslib.gpg.exceptions.KeyNotFoundError:
        gpg signing errors.

    Side Effects:
      Calls system gpg command in a subprocess.

    Returns:
      The signature. Format is securesystemslib.formats.GPG_SIGNATURE_SCHEMA.

    """
    signature = securesystemslib.gpg.functions.create_signature(
        self.signed.signable_bytes, gpg_keyid, gpg_home)

    self.signatures.append(signature)

    return signature


  def verify_sigs(self, keys: List[Key], threshold):
    """Verifies signature over signable in signatures with a list of keys.

    Uses the UTF-8 encoded canonical JSON byte representation of the signable
    attribute to verify the signature deterministically.

    Arguments:
        keys: A list of public keys to verify the signatures.
        threshold: Number of signatures needed to pass the verification.

    Raises:
        ValueError: If "threshold" is not valid.
        SignatureVerificationError: If the enclosed signatures do not pass
            the verification.

    Returns:
        accepted_keys: A dict of unique public keys.
    """

    accepted_keys = {}
    pae = self.signed.signable_bytes

    # checks for threshold value.
    if threshold <= 0:
      raise ValueError("Threshold must be greater than 0")

    if len(keys) < threshold:
      raise ValueError("Number of keys can't be less than threshold")

    for signature in self.signatures:

      # GPGSignature/ Signature from_dict method destroys the signature dict,
      # Hence, deepcopy of signature is created.
      if securesystemslib.formats.GPG_SIGNATURE_SCHEMA.matches(signature):
        signature = GPGSignature.from_dict(copy.deepcopy(signature))

      elif securesystemslib.formats.SIGNATURE_SCHEMA.matches(signature):
        signature = Signature.from_dict(copy.deepcopy(signature))

      else:
        raise SignatureVerificationError

      for key in keys:
        # If Signature keyid doesn't match with Key, skip.
        if not key.match_keyid(signature.keyid):
          continue

        # If a key verifies the signature, we exit and use the result.
        if key.verify(signature, pae):
          accepted_keys[key.keyid] = key
          break

      # Break, if amount of recognized_signer are more than threshold.
      if len(accepted_keys) >= threshold:
        break

    if threshold > len(accepted_keys):
      raise SignatureVerificationError(
          "Accepted signatures do not match threshold,"
          f" Found: {len(accepted_keys)}, Expected {threshold}"
      )

    return accepted_keys


  def verify_signature(self, verification_key):
    """Verifies a signature over signable in signatures with verification_key.

    Uses the UTF-8 encoded canonical JSON byte representation of the signable
    attribute to verify the signature deterministically.

    NOTE: Only the first signature in the signatures attribute, whose keyid
    matches the verification_key keyid, is verified. If the verification_key
    format is securesystemslib.formats.GPG_PUBKEY_SCHEMA, subkey keyids are
    considered too.

    Arguments:
      verification_key: A verification key. The format is
          securesystemslib.formats.ANY_VERIFICATION_KEY_SCHEMA.

    Raises:
      securesystemslib.exceptions.FormatError: The passed key is malformed.

      SignatureVerificationError: No signature keyid matches the verification
          key keyid, or the matching signature is malformed, or the matching
          signature is invalid.

      securesystemslib.gpg.exceptions.KeyExpirationError: Passed verification
          key is an expired gpg key.

    """
    securesystemslib.formats.ANY_VERIFICATION_KEY_SCHEMA.check_match(
        verification_key)
    verification_keyid = verification_key["keyid"]

    # Find a signature that corresponds to the keyid of the passed
    # verification key or one of its subkeys
    signature = None
    for signature in self.signatures:
      if signature["keyid"] == verification_keyid:
        break

      if signature["keyid"] in list(
          verification_key.get("subkeys", {}).keys()):
        break

    else:
      raise SignatureVerificationError("No signature found for key '{}'"
          .format(verification_keyid))

    if securesystemslib.formats.GPG_SIGNATURE_SCHEMA.matches(signature):
      valid = securesystemslib.gpg.functions.verify_signature(signature,
          verification_key, self.signed.signable_bytes)

    elif securesystemslib.formats.SIGNATURE_SCHEMA.matches(signature):
      valid = securesystemslib.keys.verify_signature(
          verification_key, signature, self.signed.signable_bytes)

    else:
      valid = False

    if not valid:
      raise SignatureVerificationError("Invalid signature for keyid '{}'"
          .format(verification_keyid))


  def _validate_signed(self):
    """Private method to check if the 'signed' attribute contains a valid
    Layout or Link object. """

    if not (isinstance(self.signed, Layout) or isinstance(self.signed, Link)):
      raise securesystemslib.exceptions.FormatError("The Metblock's 'signed'"
        " property has has to be of type 'Link' or 'Layout'.")

    # If the signed object is a Link or Layout object validate it.
    self.signed.validate()


  def _validate_signatures(self):
    """Private method to check that the 'signatures' attribute is a list of
    signatures in the format 'securesystemslib.formats.ANY_SIGNATURE_SCHEMA'.
    """

    if not isinstance(self.signatures, list):
      raise securesystemslib.exceptions.FormatError("The Metablock's"
        " 'signatures' property has to be of type 'list'.")

    for signature in self.signatures:
      securesystemslib.formats.ANY_SIGNATURE_SCHEMA.check_match(signature)

  def get_payload(self):
    """Returns signed of the Metablock."""

    return self.signed
