
import attr
import canonicaljson
import matchrule

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

  def sign(self, key):
    """ Signs the canonical JSON repr of itself (without the signatures property)
    and adds the signatures to its signature properties. """

    payload = attr.asdict(self)
    payload.pop("signatures")
    payload = canonicaljson.encode_pretty_printed_json(payload)

    signature = ssl_crypto__keys.create_signature(key, payload)
    self.signatures.append(signature)

