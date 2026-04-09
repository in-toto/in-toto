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

import json
from copy import deepcopy
from typing import Union

import attr
import securesystemslib._gpg.functions
import securesystemslib.exceptions
import securesystemslib.formats
from securesystemslib.dsse import Envelope as SSlibEnvelope
from securesystemslib.exceptions import (
    UnverifiedSignatureError,
    VerificationError,
)
from securesystemslib.signer import Key, Signature, Signer

from in_toto.exceptions import InvalidMetadata, SignatureVerificationError
from in_toto.formats import _check_public_key, _check_signature
from in_toto.models._signer import GPGSigner
from in_toto.models.common import Signable, ValidationMixin
from in_toto.models.layout import Layout
from in_toto.models.link import Link

ENVELOPE_PAYLOAD_TYPE = "application/vnd.in-toto+json"


class Metadata:
    """A Metadata abstraction between DSSE Envelope and Metablock."""

    @classmethod
    def from_dict(cls, data):
        """Loads DSSE or Traditional Metadata from its JSON/dict representation."""

        if "payload" in data:
            if data.get("payloadType") == ENVELOPE_PAYLOAD_TYPE:
                return Envelope.from_dict(data)

        elif "signed" in data:
            return Metablock.from_dict(data)

        raise InvalidMetadata

    def to_dict(self):
        """Returns the JSON-serializable dictionary representation of self."""
        raise NotImplementedError  # pragma: no cover

    @classmethod
    def load(cls, path):
        """Loads the JSON string representation of metadata from disk.

        Arguments:
          path: The path to read the file from.

        Raises:
          IOError: The file cannot be read.
          InvalidMetadata: Metadata format is invalid.
          securesystemslib.exceptions.FormatError: Metadata format is invalid.

        Returns:
          A Metadata containing a Link or Layout object.

        """
        with open(path, encoding="utf8") as fp:
            data = json.load(fp)

        return cls.from_dict(data)

    def dump(self, path):
        """Writes the JSON string representation of the instance to disk.

        Arguments:
          path: The path to write the file to.

        Raises:
          IOError: File cannot be written.

        """
        json_bytes = json.dumps(
            self.to_dict(),
            sort_keys=True,
        ).encode("utf-8")

        with open(path, "wb") as fp:
            fp.write(json_bytes)

    def create_signature(self, signer: Signer) -> Signature:
        """Creates and adds signature over signable representation of self.

        The passed signer is used for signing. Applications can implement their
        own signer or use one from ``securesystemslib``.

        Arguments:
            signer: A ``Signer`` implementation.

        Returns:
            The ``Signature`` object returned from ``Signer``.

        """
        raise NotImplementedError  # pragma: no cover

    def verify_signature(self, verification_key):
        """Verifies a signature over signable in signatures with verification_key.

        Arguments:
          verification_key: A verification key.

        Raises:
          securesystemslib.exceptions.FormatError: The passed key is malformed.

          SignatureVerificationError: No signature keyid matches
              the verification key keyid, or the matching signature is malformed,
              or the matching signature is invalid.
        """
        raise NotImplementedError  # pragma: no cover

    def get_payload(self):
        """Returns ``Link`` or ``Layout``."""
        raise NotImplementedError  # pragma: no cover


class Envelope(SSlibEnvelope, Metadata):
    """DSSE Envelope for in-toto payloads."""

    @classmethod
    def from_signable(cls, signable: Signable) -> "Envelope":
        """Creates DSSE envelope with signable bytes as payload.

        Note:
        The method accepts a `Signable` because it serves as a base class
        for `Link` and `Layout`.
        This method intentionally avoids using `Signable.signable_bytes` to
        prevent canonicalization, which is contrary to DSSE's design principles.
        Instead, this method serializes the `Signable` using regular JSON.

        Arguments:
            signable (Signable): The object to be signed. This object is expected
                to be compatible with `Signable`, but its `signable_bytes` property
                will not be used.

        Returns:
            Envelope: An envelope containing the serialized signable object.
        """

        # Serialize the signable object to JSON bytes without canonicalization
        json_bytes = json.dumps(
            attr.asdict(signable),
            sort_keys=True,
        ).encode("utf-8")

        # Create and return the envelope
        return cls(
            payload=json_bytes,
            payload_type=ENVELOPE_PAYLOAD_TYPE,
            signatures={},
        )

    def create_signature(self, signer: Signer) -> Signature:
        if isinstance(signer, GPGSigner):
            raise NotImplementedError("GPG Signing is not implemented")

        return super().sign(signer)

    def verify_signature(self, verification_key):
        # Deepcopy to preserve `verification_key`, which might still be needed
        # in calling context and would otherwise be destroyed in `from_dict`.
        # NOTE: It would be nice to support `Key` natively in in-toto model.
        key = Key.from_dict(
            verification_key["keyid"], deepcopy(verification_key)
        )

        try:
            super().verify(keys=[key], threshold=1)
        except VerificationError as exc:
            raise SignatureVerificationError from exc

    def get_payload(self) -> Union[Link, Layout]:
        """Parse DSSE payload into Link or Layout object.

        Raises:
            InvalidMetadata: If type in payload is not ``link`` or ``layout``.

        Returns:
            Link or Layout.
        """

        data = json.loads(self.payload.decode("utf-8"))
        _type = data.get("_type")
        if _type == "link":
            return Link.read(data)
        if _type == "layout":
            return Layout.read(data)

        raise InvalidMetadata


@attr.s(repr=False, init=False)
class Metablock(Metadata, ValidationMixin):
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
        """Returns the JSON string representation."""
        indent = None if self.compact_json else 1
        separators = (",", ":") if self.compact_json else (",", ": ")

        return json.dumps(
            {"signatures": self.signatures, "signed": attr.asdict(self.signed)},
            indent=indent,
            separators=separators,
            sort_keys=True,
        )

    def dump(self, path):
        """Writes the JSON string representation of the instance to disk.

        Arguments:
          path: The path to write the file to.

        Raises:
          IOError: File cannot be written.

        """
        with open(path, "wb") as fp:
            fp.write(f"{self}".encode())

    @classmethod
    def from_dict(cls, data):
        """Creates a Metablock object from its JSON/dict representation."""

        signatures = data.get("signatures", [])
        signed_data = data.get("signed", {})
        signed_type = signed_data.get("_type")

        if signed_type == "link":
            signed = Link.read(signed_data)

        elif signed_type == "layout":
            signed = Layout.read(signed_data)

        else:
            raise securesystemslib.exceptions.FormatError(
                "Invalid Metadata format"
            )

        return cls(signatures=signatures, signed=signed)

    def to_dict(self):
        """Returns the JSON-serializable dictionary representation of self."""

        return {
            "signatures": self.signatures,
            "signed": attr.asdict(self.signed),
        }

    @property
    def type_(self):
        """A shortcut to the `type_` attribute of the object on the signable
        attribute (should be one of "link" or "layout")."""
        # NOTE: Trailing underscore is used by convention (pep8) to avoid conflict
        # with Python's type keyword.
        return self.signed.type_

    def create_signature(self, signer: Signer):
        signature = signer.sign(self.signed.signable_bytes)
        self.signatures.append(signature.to_dict())

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
      ValueError, OSError, securesystemslib._gpg.exceptions.CommandError, \
            securesystemslib._gpg.exceptions.KeyNotFoundError:
        gpg signing errors.

    Side Effects:
      Calls system gpg command in a subprocess.

    Returns:
      The signature.

    """
        signature = securesystemslib._gpg.functions.create_signature(  # noqa: SLF001
            self.signed.signable_bytes, gpg_keyid, gpg_home
        )

        self.signatures.append(signature)

        return signature

    def verify_signature(self, verification_key):
        """Verifies a signature over signable in signatures with verification_key.

        Uses the UTF-8 encoded canonical JSON byte representation of the signable
        attribute to verify the signature deterministically.

        NOTE: Only the first signature in the signatures attribute, whose keyid
        matches the verification_key keyid, is verified. If the verification_key
        is a gpg key, subkey keyids are considered too.

        Arguments:
          verification_key: A verification key.

        Raises:
          securesystemslib.exceptions.FormatError: The passed key is malformed.

          SignatureVerificationError: No signature keyid matches the verification
              key keyid, or the matching signature is malformed, or the matching
              signature is invalid.

          securesystemslib._gpg.exceptions.KeyExpirationError: Passed verification
              key is an expired gpg key.

        """
        _check_public_key(verification_key)
        verification_keyid = verification_key["keyid"]

        # Find a signature that corresponds to the keyid of the passed
        # verification key or one of its subkeys
        signature = None
        for signature in self.signatures:
            if signature["keyid"] == verification_keyid:
                break

            if signature["keyid"] in list(
                verification_key.get("subkeys", {}).keys()
            ):
                break

        else:
            raise SignatureVerificationError(
                f"No signature found for key '{verification_keyid}'"
            )

        valid = False
        if "signature" in signature and "other_headers" in signature:
            valid = securesystemslib._gpg.functions.verify_signature(  # noqa: SLF001
                signature, verification_key, self.signed.signable_bytes
            )

        else:
            # Parse key and (below) signature dicts as `Key` and `Signature`
            # instances to use modern securesystemslib verification code.
            # Deepcopy to preserve original dicts, which are otherwise destroyed
            # in `from_dict` methods.
            # NOTE: It would be nice to support `Key` and `Signature` natively
            # in in-toto model classes.
            key = Key.from_dict(verification_keyid, deepcopy(verification_key))

            try:
                sig = Signature.from_dict(deepcopy(signature))
                key.verify_signature(sig, self.signed.signable_bytes)
                valid = True

            except (KeyError, UnverifiedSignatureError):
                pass

        if not valid:
            raise SignatureVerificationError(
                f"Invalid signature for keyid '{verification_keyid}'"
            )

    def _validate_signed(self):
        """Private method to check if the 'signed' attribute contains a valid
        Layout or Link object."""

        if not isinstance(self.signed, (Layout, Link)):
            raise securesystemslib.exceptions.FormatError(
                "The Metablock's 'signed'"
                " property has to be of type 'Link' or 'Layout'."
            )

        # If the signed object is a Link or Layout object validate it.
        self.signed.validate()

    def _validate_signatures(self):
        """Private method to check that the 'signatures' attribute is valid."""

        if not isinstance(self.signatures, list):
            raise securesystemslib.exceptions.FormatError(
                "The Metablock's"
                " 'signatures' property has to be of type 'list'."
            )

        for signature in self.signatures:
            _check_signature(signature)

    def get_payload(self):
        """Returns signed of the Metablock."""

        return self.signed
