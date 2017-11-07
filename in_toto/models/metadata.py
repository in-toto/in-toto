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
import canonicaljson

import securesystemslib.keys
import securesystemslib.formats
import securesystemslib.exceptions

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
    """Returns a JSON string representation of the object."""
    # the double {{'s is the escape sequence for an individual {. We wrap this
    # under a format string to avoid encoding to json twice (which turns a json
    # string into a string and so on...
    # FIXME:
    # We are mixing 3 JSON string formats here: The value of "signed" is
    # "pretty printed canonical json", the value of "signatures" is
    # "canonical json" and the container is just "json".
    # Is this really what we want?
    return '{{"signed": {}, "signatures": {}}}'.format(self.signed,
        canonicaljson.encode_canonical_json(self.signatures))


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
  def _type(self):
    """ Shortcut to the _type property of the contained Link or Layout object,
    should be one of "link" or "layout". """
    return self.signed._type


  def sign(self, key):
    """
    <Purpose>
      Signs the pretty printed canonical JSON representation
      (see models.common.Signable.__repr__) of the Link or Layout object
      contained in the `signed` property with the passed key and appends the
      created signature to `signatures`.

    <Arguments>
      key:
              A signing key in the format securesystemslib.formats.KEY_SCHEMA

    <Returns>
      None.

    """
    securesystemslib.formats.KEY_SCHEMA.check_match(key)

    signature = securesystemslib.keys.create_signature(key, repr(self.signed))
    self.signatures.append(signature)


  def verify_signatures(self, keys_dict):
    """
    <Purpose>
      Verifies all signatures found in the `signatures` property using the keys
      from the passed dictionary of keys and the pretty printed canonical JSON
      representation (see models.common.Signable.__repr__) of the Link or
      Layout object contained in `signed`.

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
              securesystemslib.formats.KEYDICT_SCHEMA

    <Exceptions>
      FormatError
            if the passed key dictionary is not conformant with
            securesystemslib.formats.KEYDICT_SCHEMA

      SignatureVerificationError
            if the Metablock is not signed

            if the Metablock carries a signature for which no key is found in
            the passed key dictionary, which means that multiple signatures
            have to be verified at once

            if any of the verified signatures is actually broken

    <Returns>
      None.

    """
    securesystemslib.formats.KEYDICT_SCHEMA.check_match(keys_dict)

    if not self.signatures or len(self.signatures) <= 0:
      raise SignatureVerificationError("No signatures found")

    for signature in self.signatures:
      keyid = signature["keyid"]
      try:
        key = keys_dict[keyid]
      except KeyError:
        raise SignatureVerificationError(
            "Signature key not found, key id is '{0}'".format(keyid))
      if not securesystemslib.keys.verify_signature(
          key, signature, repr(self.signed)):
        raise SignatureVerificationError("Invalid signature")