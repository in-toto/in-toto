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
  Provides base classes for various classes in the model.

<Classes>
  Metablock:
      pretty printed canonical JSON representation and dump

"""

import attr
import canonicaljson

import securesystemslib.keys
import securesystemslib.formats
import securesystemslib.exceptions
from in_toto.models.common import Signable
from in_toto.exceptions import SignatureVerificationError

@attr.s(repr=False, init=False)
class Metablock(object):
  """ This object holds the in-toto metablock data structure. This includes
  the fields "signed" and "signatures", i.e., what was signed and the
  signatures. Other convenience classes will inherit this class to provide
  serialization and signing capabilities to in-toto metadata.
  """
  signatures = attr.ib()
  signed = attr.ib()


  def __init__(self, **kwargs):
    self.signatures = kwargs.get("signatures", [])
    self.signed = kwargs.get("signed")


  """Objects with base class Metablock have a __repr__ method
  that returns a canonical pretty printed JSON string and can be dumped to a
  file """
  def __repr__(self):
    # the double {{'s is the escape sequence for an individual {. We wrap this
    # under a format string to avoid encoding to json twice (which turns a json
    # string into a string and so on...
    return '{{"signed": {}, "signatures": {}}}'.format(self.signed,
        canonicaljson.encode_canonical_json(self.signatures))

  def dump(self, filename):
    with open(filename, 'wt') as fp:
      fp.write("{}".format(self))


  @staticmethod
  def load(path):
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
    return self.signed._type


  def sign(self, key):
    """Signs the canonical JSON representation of itself (without the
    signatures property) and adds the signatures to its signature properties."""

    securesystemslib.formats.KEY_SCHEMA.check_match(key)

    signature = securesystemslib.keys.create_signature(key, repr(self.signed))
    self.signatures.append(signature)


  def verify_signatures(self, keys_dict):
    """Verifies all signatures of the object using the passed key_dict."""

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