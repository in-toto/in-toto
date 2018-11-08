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
import json

import securesystemslib.keys
import securesystemslib.formats
import securesystemslib.exceptions

import in_toto.formats
import in_toto.gpg.functions

from in_toto.models.common import ValidationMixin
from in_toto.models.link import Link
from in_toto.models.layout import Layout
from in_toto.exceptions import SignatureVerificationError

@attr.s(repr=False, init=False)
class Metablock(ValidationMixin):
  """ This object holds the in-toto metablock data structure. This includes
  the fields "signed" and "signatures", i.e., what was signed and the
  signatures. """
  signatures = attr.ib()
  signed = attr.ib()


  def __init__(self, **kwargs):
    self.signatures = kwargs.get("signatures", [])
    self.signed = kwargs.get("signed")
    self.compact_json = kwargs.get("compact_json", False)

    self.validate()


  def __repr__(self):
    """Returns an indented JSON string of the metadata object. """
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


  def dump(self, filename):
    """
    <Purpose>
      Write the JSON string representation of the Metablock object
      to disk.

    <Arguments>
      filename:
              The path to write the file to.

    <Side Effects>
      Writing metadata file to disk

    <Returns>
      None.

    """
    with open(filename, "wb") as fp:
      fp.write("{}".format(self).encode("utf-8"))


  @staticmethod
  def load(path):
    """
    <Purpose>
      Loads the JSON string representation of signed metadata from disk
      and creates a Metablock object.
      The `signed` attribute of the Metablock object is assigned a Link
      or Layout object, depending on the `_type` field in the loaded
      metadata file.

    <Arguments>
      path:
              The path to write the file to.

    <Side Effects>
      Reading metadata file from disk

    <Returns>
      None.

    """
    with open(path, "r") as fp:
      data = json.load(fp)

    signatures = data.get("signatures", [])
    signed_data = data.get("signed", {})
    signed_type = signed_data.get("_type")

    if signed_type == "link":
      signed = Link.read(signed_data)

    elif signed_type == "layout":
      signed = Layout.read(signed_data)

    else:
      raise securesystemslib.exceptions.FormatError("Invalid Metadata format")

    return Metablock(signatures=signatures, signed=signed)


  @property
  def type_(self):
    """Shortcut to the _type property of the contained Link or Layout object,
    should be one of "link" or "layout". Trailing underscore used by
    convention (pep8) to avoid conflict with Python's type keyword. """
    return self.signed.type_


  def sign(self, key):
    """
    <Purpose>
      Signs the utf-8 encoded canonical JSON bytes of the Link or Layout object
      contained in `self.signed` with the passed key and appends the created
      signature to `self.signatures`.

      Note: We actually pass the dictionary representation of the data to be
      signed and `securesystemslib.keys.create_signature` converts it to
      canonical JSON utf-8 encoded bytes before creating the signature.

    <Arguments>
      key:
              A signing key in the format securesystemslib.formats.KEY_SCHEMA

    <Returns>
      The dictionary representation of the newly created signature.

    """
    securesystemslib.formats.KEY_SCHEMA.check_match(key)

    signature = securesystemslib.keys.create_signature(key,
        self.signed.signable_dict)

    self.signatures.append(signature)

    return signature

  def sign_gpg(self, gpg_keyid=None, gpg_home=None):
    """
    <Purpose>
      Signs the utf-8 encoded canonical JSON bytes of the Link or Layout object
      contained in `self.signed` using `gpg.functions.gpg_sign_object` and
      appends the created signature to `self.signatures`.

    <Arguments>
      gpg_keyid: (optional)
              A gpg keyid, if omitted the default signing key is used

      gpg_home: (optional)
              The path to the gpg keyring, if omitted the default gpg keyring
              is used

    <Returns>
      The dictionary representation of the newly created signature.

    """
    signature = in_toto.gpg.functions.gpg_sign_object(
        self.signed.signable_bytes, gpg_keyid, gpg_home)

    self.signatures.append(signature)

    return signature


  def verify_signature(self, verification_key):
    """
    <Purpose>
      Verifies the signature, found in `self.signatures`, corresponding to the
      passed verification key, or in case of GPG one of its subkeys, identified
      by the key's keyid, using the passed verification key and the utf-8
      encoded canonical JSON bytes of the Link or Layout object, contained in
      `self.signed`.

      If the signature matches `in_toto.gpg.formats.SIGNATURE_SCHEMA`,
      `in_toto.gpg.functions.gpg_verify_signature` is used for verification,
      if the signature matches `securesystemslib.formats.SIGNATURE_SCHEMA`
      `securesystemslib.keys.verify_signature` is used.

      Note: In case of securesystemslib we actually pass the dictionary
      representation of the data to be verified and
      `securesystemslib.keys.verify_signature` converts it to
      canonical JSON utf-8 encoded bytes before verifying the signature.

    <Arguments>
      verification_key:
              Verifying key in the format:
              in_toto.formats.ANY_VERIFICATION_KEY_SCHEMA

    <Exceptions>
      FormatError
            If the passed key is not conformant with
            `in_toto.formats.ANY_VERIFICATION_KEY_SCHEMA`

      SignatureVerificationError
            If the Metablock does not carry a signature signed with the
            private key corresponding to the passed verification key or one
            of its subkeys

            If the signature corresponding to the passed verification key or
            one of its subkeys does not match securesystemslib's or
            in_toto.gpg's signature schema.

            If the signature to be verified is malformed or invalid.

    <Returns>
      None.

    """
    in_toto.formats.ANY_VERIFICATION_KEY_SCHEMA.check_match(verification_key)
    verification_keyid = verification_key["keyid"]

    # Find a signature that corresponds to the keyid of the passed
    # verification key or one of its subkeys
    signature = None
    for signature in self.signatures:
      if signature["keyid"] == verification_keyid:
        break

      elif signature["keyid"] in list(
          verification_key.get("subkeys", {}).keys()):
        break

    else:
      raise SignatureVerificationError("No signature found for key '{}'"
          .format(verification_keyid))

    if in_toto.gpg.formats.SIGNATURE_SCHEMA.matches(signature):
      valid = in_toto.gpg.functions.gpg_verify_signature(signature,
          verification_key, self.signed.signable_bytes)

    elif securesystemslib.formats.SIGNATURE_SCHEMA.matches(signature):
      valid = securesystemslib.keys.verify_signature(
          verification_key, signature, self.signed.signable_dict)

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
    signatures in the format 'in_toto.formats.ANY_SIGNATURE_SCHEMA'. """

    if not isinstance(self.signatures, list):
      raise securesystemslib.exceptions.FormatError("The Metablock's"
        " 'signatures' property has to be of type 'list'.")

    for signature in self.signatures:
      in_toto.formats.ANY_SIGNATURE_SCHEMA.check_match(signature)
