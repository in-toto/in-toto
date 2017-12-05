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

from in_toto.models.link import Link
from in_toto.models.layout import Layout
from in_toto.exceptions import SignatureVerificationError

@attr.s(repr=False, init=False)
class Metablock(object):
  """ This object holds the in-toto metablock data structure. This includes
  the fields "signed" and "signatures", i.e., what was signed and the
  signatures. """
  signatures = attr.ib()
  signed = attr.ib()


  def __init__(self, **kwargs):
    self.signatures = kwargs.get("signatures", [])
    self.signed = kwargs.get("signed")


  def __repr__(self):
    """Returns an indented JSON string of the metadata object. """
    return json.dumps(
        {
          "signatures": self.signatures,
          "signed": attr.asdict(self.signed)
        }, indent=1, separators=(",", ": "), sort_keys=True)


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
    with open(filename, "wt") as fp:
      fp.write("{}".format(self))


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
      Signs the pretty printed canonical JSON representation of the Link or
      Layout object contained in the `signed` property with the passed key and
      appends the created signature to `signatures`.

    <Arguments>
      key:
              A signing key in the format securesystemslib.formats.KEY_SCHEMA

    <Returns>
      The newly created signature dictionary.

    """
    securesystemslib.formats.KEY_SCHEMA.check_match(key)

    # We actually pass the dictionary representation of the data to sign
    # and securesystemslib converts it to canonical JSON utf-8 encoded bytes
    # before creating the signature.
    signature = securesystemslib.keys.create_signature(key,
        self.signed.signable_dict)

    self.signatures.append(signature)

    return signature

  def sign_gpg(self, gpg_keyid=None, gpg_home=None):
    """
    <Purpose>
      Signs the pretty printed canonical JSON representation
      (see models.common.Signable.signable_bytes) of the Link or Layout object
      contained in the `signed` property using `gpg_verify_signature` and
      appends the created signature to `signatures`.

    <Arguments>
      gpg_keyid: (optional)
              A gpg keyid, if omitted the default signing key is used

      gpg_home: (optional)
              The path to the gpg keyring, if omitted the default gpg keyring
              is used

    <Returns>
      The newly created signature dictionary.

    """
    signature = in_toto.gpg.functions.gpg_sign_object(
        self.signed.signable_bytes, gpg_keyid, gpg_home)

    self.signatures.append(signature)

    return signature


  def verify_signatures(self, keys_dict):
    """
    <Purpose>
      Verifies all signatures found in the `signatures` property using the keys
      from the passed dictionary of keys and the pretty printed canonical JSON
      representation (see models.common.Signable.signable_bytes) of the Link or
      Layout object contained in `signed`.

      If the signature matches `in_toto.gpg.formats.SIGNATURE_SCHEMA`,
      `in_toto.gpg.functions.gpg_verify_signature` is used for verification,
      `securesystemslib.keys.verify_signature` is used otherwise.

      Verification fails if,
        - the passed keys don't have the right format,
        - the object is not signed,
        - there is a signature for which no key was passed,
        - if any of the signatures is actually broken.

      Note:
      This will be revised with in-toto/in-toto#135

    <Arguments>
      keys_dict:
              Verifying keys in the format:
              in_toto.formats.ANY_VERIFY_KEY_DICT_SCHEMA

    <Exceptions>
      FormatError
            if the passed key dictionary is not conformant with
            in_toto.formats.ANY_VERIFY_KEY_DICT_SCHEMA

      SignatureVerificationError
            if the Metablock is not signed

            if the Metablock carries a signature for which no key is found in
            the passed key dictionary, which means that multiple signatures
            have to be verified at once

            if any of the verified signatures is actually broken

    <Returns>
      None.

    """
    in_toto.formats.ANY_VERIFY_KEY_DICT_SCHEMA.check_match(keys_dict)

    if not self.signatures or len(self.signatures) <= 0:
      raise SignatureVerificationError("No signatures found")

    for signature in self.signatures:
      keyid = signature["keyid"]
      try:
        key = keys_dict[keyid]

      except KeyError:
        raise SignatureVerificationError(
            "Signature key not found, key id is '{0}'".format(keyid))

      if in_toto.gpg.formats.SIGNATURE_SCHEMA.matches(signature):
        valid = in_toto.gpg.functions.gpg_verify_signature(signature, key,
            self.signed.signable_bytes)

      else:
        # We actually pass the dictionary representation of the data to verify
        # and securesystemslib converts it to canonical JSON utf-8 encoded
        # bytes before verifying the signature.
        valid = securesystemslib.keys.verify_signature(
            key, signature, self.signed.signable_dict)

      if not valid:
        raise SignatureVerificationError("Invalid signature")
