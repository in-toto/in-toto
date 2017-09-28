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

"""

import attr
import canonicaljson
import inspect

import securesystemslib.keys
import securesystemslib.formats
from in_toto.exceptions import SignatureVerificationError

@attr.s(repr=False, init=False)
class Metablock(object):
  """ This object holds the in-toto metablock data structure. This includes
  the fields "signed" and "signatures", i.e., what was signed and the
  signatures. Other convenience classes will inherit this class to provide
  serialization and signing capabilities to in-toto metadata.
  """

  def __init__(self, **kwargs):
    """ The constructor of metablock requires subclasses to implement a
    template for its underlying signable class (see get_signable()). This
    method will populate the signatures list and instantiate the subclass's
    corresponding signable under its signed property"""
    self.signatures = []
    if "signatures" in kwargs:
      self.signatures = kwargs['signatures']
      del kwargs['signatures']

    signable = self.get_signable()
    if 'signed' in kwargs:
      if isinstance(kwargs['signed'], Signable):
        self.signed = kwargs['signed']
      else:
        self.signed = signable(**kwargs['signed'])
    else:
      self.signed = signable()

  def get_signable(self):
    """ There should not be an instance of metablock, as it is an abstract
    class. Its subclasses (Layout, Link) should implement the get_signable
    method to return the corresponding signable class to populate """
    raise NotImplementedError('Metablock is not intended to be instantiated. '
        'You probably wanted to instantiate a Layout or a Link?')

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

  def sign(self, key):
    """Signs the canonical JSON representation of itself (without the
    signatures property) and adds the signatures to its signature properties."""

    securesystemslib.formats.KEY_SCHEMA.check_match(key)

    signature = securesystemslib.keys.create_signature(key, repr(self.signed))
    self.signatures.append(signature)

  """ FIXME: This is mostly syntactic sugar and backwards compatibility stuff.
  This method is added to stop the code from breaking as old instances to
  (e.g.,) Layout.[property] should now be Layout.signed.[property]. With time
  we should phase these instances out.
  """
  def __getattr__(self, item):
    if item == 'signatures' or item == 'signed':
      return None

    try:
      return self.signed.__dict__[item]
    except KeyError:
      raise AttributeError

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

class ValidationMixin(object):
  """ The validation mixin provides a self-inspecting method, validate, to
  allow in-toto's objects to check that they are proper. """

  def validate(self):
    """
      <Purpose>
        Inspects the class (or subclass) for validate methods to ensure the
        all its members are properly formed. This method can be used to ensure
        the metadata contained in this class is proper before calling dump.

      <Arguments>
        None

      <Exceptions>
        FormatError: If any of the members of this class are not properly
                     populated.

      <Side Effects>
        None

      <Returns>
        None
    """
    for method in inspect.getmembers(self, predicate=inspect.ismethod):
        if method[0].startswith("_validate_"):
          method[1]()

@attr.s(repr=False, init=False)
class Signable(ValidationMixin):
  """Objects with base class Signable are to be included in a Metablock class
  to be signed (hence the name). They provide a pretty-printed json
  representation of its fields"""

  def __repr__(self):
    return canonicaljson.encode_pretty_printed_json(attr.asdict(self))
