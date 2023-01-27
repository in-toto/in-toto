# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  gpg.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Jan 26, 2023

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides in-toto flavored GPGSigner, GPGSignature and GPGKey.

"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import securesystemslib.gpg.functions as gpg
from securesystemslib.signer import Key, Signature, Signer, SecretsHandler


class _LegacyGPGSignature(Signature):
  """A container class containing information about a gpg signature.
  Besides the signature, it also contains other meta information
  needed to uniquely identify the key used to generate the signature.

  Attributes:
    keyid: HEX string used as a unique identifier of the key.
    signature: HEX string representing the signature.
    other_headers: HEX representation of additional GPG headers.
  """

  def __init__(
    self,
    keyid: str,
    signature: str,
    other_headers: str,
  ):
    super().__init__(keyid, signature)
    self.other_headers = other_headers

  @classmethod
  def from_dict(cls, signature_dict: Dict) -> "_LegacyGPGSignature":
    """Creates a ``_LegacyGPGSignature`` object from its JSON/dict
    representation.

    Arguments:
      signature_dict: Dict containing valid "keyid", "signature" and
        "other_fields" fields.
    Raises:
      KeyError: If any of the "keyid", "sig" or "other_headers" fields
        are missing from the signature_dict.
    Returns:
      ``_LegacyGPGSignature`` instance.
    """

    return cls(
      signature_dict["keyid"],
      signature_dict["signature"],
      signature_dict["other_headers"],
    )

  def to_dict(self) -> Dict:
    """Returns the JSON-serializable dictionary representation of self."""
    return {
      "keyid": self.keyid,
      "signature": self.signature,
      "other_headers": self.other_headers,
    }


class _LegacyGPGSigner(Signer):
  """A in-toto gpg implementation of the ``Signer`` interface.
  Provides a sign method to generate a cryptographic signature with gpg, using
  an RSA, DSA or EdDSA private key identified by the keyid on the instance.

  Arguments:
    keyid: The keyid of the gpg signing keyid. If not passed the default
      key in the keyring is used.
    homedir: Path to the gpg keyring. If not passed the default keyring
      is used.
  """

  def __init__(
    self,
    keyid: Optional[str] = None,
    homedir: Optional[str] = None
  ):
    self.keyid = keyid
    self.homedir = homedir

  @classmethod
  def from_priv_key_uri(
    cls,
    priv_key_uri: str,
    public_key: Key,
    secrets_handler: Optional[SecretsHandler] = None
  ) -> "_LegacyGPGSigner":

    raise NotImplementedError("Incompatible with private key URIs")

  def sign(self, payload: bytes) -> _LegacyGPGSignature:
    """Signs a given payload by the key assigned to the ``_LegacyGPGSigner``
    instance. Calls the gpg command line utility to sign the passed content
    with the key identified by the passed keyid from the gpg keyring at the
    passed homedir.

    The executed base command is defined in
    securesystemslib.gpg.constants.GPG_SIGN_COMMAND.

    Arguments:
      payload: The bytes to be signed.
    Raises:
      securesystemslib.exceptions.FormatError:
        If the keyid was passed and does not match
        securesystemslib.formats.KEYID_SCHEMA.
      ValueError: the gpg command failed to create a valid signature.
      OSError: the gpg command is not present or non-executable.
      securesystemslib.exceptions.UnsupportedLibraryError: the gpg command is
        not available, or the cryptography library is not installed.
      securesystemslib.gpg.exceptions.CommandError: the gpg command returned a
        non-zero exit code.
      securesystemslib.gpg.exceptions.KeyNotFoundError: the used gpg version is
        not fully supported and no public key can be found for short keyid.
      Returns:
        Returns a ``_LegacyGPGSignature`` class instance.
    """

    sig_dict = gpg.create_signature(payload, self.keyid, self.homedir)
    return _LegacyGPGSignature(**sig_dict)


@dataclass
class _LegacyGPGKey(Key):
  """A container class representing public key portion of a GPG key.
  Provides a verify method to verify a cryptographic signature with a
  gpg-style rsa, dsa or ecdsa public key on the instance.

  Attributes:
    type: Key type, e.g. "rsa", "dsa" or "ecdsa".
    method: GPG Key Scheme, For example:
      "pgp+rsa-pkcsv1.5", "pgp+dsa-fips-180-2", and "pgp+eddsa-ed25519".
    hashes: list of GPG Hash Algorithms, e.g. "pgp+SHA2".
    keyval: Opaque key content.
    keyid: Key identifier that is unique within the metadata it is used in.
      Keyid is not verified to be the hash of a specific representation
      of the key.
    creation_time: Unix timestamp when GPG key was created.
    validity_period: Validity of the GPG Keys in days.
    subkeys: A dictionary containing keyid and GPG subkey.
  """

  type: str
  method: str
  hashes: List[str]
  keyval: Dict[str, str]
  keyid: str
  creation_time: Optional[int] = None
  validity_period: Optional[int] = None
  subkeys: Optional[Dict[str, "_LegacyGPGKey"]] = None

  @classmethod
  def from_dict(cls, keyid: str, key_dict: Dict[str, Any]):
    """Creates ``_LegacyGPGKey`` object from its json/dict representation.
    Raises:
      KeyError, TypeError: Invalid arguments.
    """
    subkeys_dict = key_dict.get("subkeys")

    gpg_subkeys = None
    if subkeys_dict:
      gpg_subkeys = {
        _keyid: _LegacyGPGKey.from_dict(_keyid, subkey_dict)
        for (_keyid, subkey_dict) in subkeys_dict.items()
      }

    return cls(
      key_dict["type"],
      key_dict["method"],
      key_dict["hashes"],
      key_dict["keyval"],
      keyid,
      key_dict.get("creation_time"),
      key_dict.get("validity_period"),
      gpg_subkeys,
    )

  def to_dict(self):
    """Returns the dictionary representation of self."""

    key_dict = {
      "method": self.method,
      "type": self.type,
      "hashes": self.hashes,
      "keyid": self.keyid,
      "keyval": self.keyval,
    }

    if self.creation_time:
      key_dict["creation_time"] = self.creation_time
    if self.validity_period:
      key_dict["validity_period"] = self.validity_period
    if self.subkeys:
      subkeys_dict = {
        keyid: subkey.to_dict()
        for (keyid, subkey) in self.subkeys.items()
      }
      key_dict["subkeys"] = subkeys_dict

    return key_dict

  @classmethod
  def from_keyring(cls, keyid, homedir=None):
    """Creates ``_LegacyGPGKey`` object from GnuPG Keyring."""

    pubkey_dict = gpg.export_pubkey(keyid, homedir)
    return cls.from_dict(keyid, pubkey_dict)

  def verify_signature(
    self,
    signature: _LegacyGPGSignature,
    data: bytes
  ) -> bool:
    """Verifies a given payload by the key assigned to the _LegacyGPGKey
    instance.

    Arguments:
      signature: A ``_LegacyGPGSignature`` class instance.
      payload: The bytes to be verified.
    Returns:
      Boolean. True if the signature is valid, False otherwise.
    """

    return gpg.verify_signature(signature.to_dict(), self.to_dict(), data)
