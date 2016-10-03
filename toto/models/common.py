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
  def payload():
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

    for signature in self.sigantures:
      if key["keyid"] == signature["keyid"]:
        return toto.ssl_crypto.keys.verify_signature(key, signature,
            self.payload)
    else:
      # XXX LP: Replace exception (or return false?)
      raise Exception("Signature with keyid not found")
