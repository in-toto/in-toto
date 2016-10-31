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

<Classes>
  Metablock:
      pretty printed canonical JSON representation and dump

  Signable:
      sign self, store signature to self and verify signatures

  ComparableHashDict: (helper class)
      compare contained dictionary of hashes using "=", "!="
"""

import attr
import canonicaljson

from ..ssl_crypto import keys as ssl_crypto__keys

@attr.s(repr=False)
class Metablock(object):
  """Objects with base class Metablock have a __repr__ method
  that returns a canonical pretty printed JSON string and can be dumped to a
  file """
  def __repr__(self):
    return canonicaljson.encode_pretty_printed_json(attr.asdict(self))

  def dump(self, filename):
    with open(filename, 'wt') as fp:
      fp.write("{}".format(self))


@attr.s(repr=False)
class Signable(Metablock):
  """Objects with base class Signable can sign their payload (a canonical
  pretty printed JSON string not containing the signatures attribute) and store
  the signature (signature format: ssl_crypto__formats.SIGNATURE_SCHEMA) """
  signatures = attr.ib([])

  @property
  def payload(self):
    payload = attr.asdict(self)
    payload.pop("signatures")
    return canonicaljson.encode_pretty_printed_json(payload)

  def sign(self, key):
    """Signs the canonical JSON representation of itself (without the
    signatures property) and adds the signatures to its signature properties."""

    # XXX LP: Todo: Verify key format

    signature = ssl_crypto__keys.create_signature(key, self.payload)
    self.signatures.append(signature)

  def verify_signatures(self, keys_dict):
    """Verifies all signatures of the object using the passed key_dict."""

    if not self.signatures or len(self.signatures) <= 0:
      raise Exception("No signatures found")

    for signature in self.signatures:
      keyid = signature["keyid"]
      try:
        key = keys_dict[keyid]
      except:
        raise Exception("Signature key not found, key id is %s" % keyid)
      if not ssl_crypto__keys.verify_signature(key, signature, self.payload):
        raise Exception("Invalid signature")


@attr.s(repr=False, cmp=False)
class ComparableHashDict(object):
  """Helper class providing that wraps hash dicts (format:
  toto.ssl_crypto.formats.HASHDICT_SCHEMA) in order to compare them using
  `=` and `!=`"""

  hash_dict = attr.ib({})

  def __eq__(self, other):
    """Equal if the dicts have the same keys and the according values
    (strings) are equal"""

    if self.hash_dict.keys() != other.hash_dict.keys():
      return False

    for key in self.hash_dict.keys():
      if self.hash_dict[key] != other.hash_dict[key]:
        return False
    return True

  def __ne__(self, other):
    return not self.__eq__(other)


# @attr.s(repr=False)
# class GenericPathList(object):
#   """ Helper class implementing __contains__ to provide <path> in <path list>
#   where <path> can start with "./" or not
#   """
#   path_list = attr.ib([])

#   def __contains__(self, item):

#     if item.startswith("./"):
#       other_item = item.lstrip("./")
#     else:
#       other_item = "./" + item

#     if item in self.path_list or \
#         other_item in self.path_list:
#       return True
#     return False
