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

"""

import json
import attr
import inspect
import securesystemslib.formats



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
  to be signed (hence the name). They provide a `signable_bytes` property
  used to create deterministic signatures. """

  def __repr__(self):
    """Returns an indented JSON string of the metadata object. """
    return json.dumps(attr.asdict(self),
        indent=1, separators=(",", ": "), sort_keys=True)

  @property
  def signable_bytes(self):
    """Returns canonical JSON utf-8 encoded bytes of Signable object dictionary
    representation.

    The bytes returned from this function are used to generate
    and verify signatures (c.f. `metadata.Metablock`). Changes to this
    function might break backwards compatibility with existing metadata. """

    return securesystemslib.formats.encode_canonical(
        attr.asdict(self)).encode("UTF-8")

  @property
  def signable_dict(self):
    """Returns the dictionary representation of Signable, which we pass to
    securesystemslib signing and verifying functions, where it gets converted
    to canonical JSON utf-8 encoded bytes before signing and verifying.

    TODO: I'd rather fully control what data is signed here and not in the
    crypto backend, i.e. pass signable_bytes to the signing/verifying
    functions. This would require a change to securesystemslib.
    """

    return attr.asdict(self)
