import attr
import canonicaljson

from ..ssl_crypto import keys as ssl_crypto__keys

@attr.s(repr=False)
class Metablock(object):
  """ Objects with Base class Metablock have a __repr__ method
  that returns a canonical pretty printed JSON string and also dumped to a
  file. """
  def __repr__(self):
    return canonicaljson.encode_pretty_printed_json(attr.asdict(self))

  def dump(self, filename):
    with open(filename, 'wt') as fp:
      fp.write("{}".format(self))

@attr.s(repr=False)
class Signable(Metablock):
  """ Objects of signable can sign themselves, i.e. their __repr__
  without the signatures property, and store the signature to a signature
  property.
  """
  signatures = attr.ib([])

  @property
  def payload(self):
    payload = attr.asdict(self)
    payload.pop("signatures")
    return canonicaljson.encode_pretty_printed_json(payload)

  def sign(self, key):
    """ Signs the canonical JSON repr of itself (without the signatures property)
    and adds the signatures to its signature properties. """

    # XXX LP: Todo: Verify key format

    signature = ssl_crypto__keys.create_signature(key, self.payload)
    self.signatures.append(signature)

  def verify_signature(self, key):
    """ Verifies if the object contains a signature matching the keyid of the
    passed key, and if the signature is valid.

    Exceptions
      Invalid key format Exception
      Signature not found Exception
    """

    # XXX LP: Todo: Verify key format

    for signature in self.signatures:
      if key["keyid"] == signature["keyid"]:
        return ssl_crypto__keys.verify_signature(key, signature,
            self.payload)
    else:
      # XXX LP: Replace exception (or return false?)
      raise Exception("Signature with keyid not found")

@attr.s(repr=False, cmp=False)
class ComparableHashDict(object):
  """ Helper class implementing __eq__/__ne__ to compare two hash_dicts
  of the format toto.ssl_crypto.formats.HASHDICT_SCHEMA """
  hash_dict = attr.ib({})

  def __eq__(self, other):

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
