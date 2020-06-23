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
    """Validates attributes of the instance.

    Raises:
      securesystemslib.formats.FormatError: An attribute value is invalid.

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
    """The UTF-8 encoded canonical JSON byte representation of the dictionary
    representation of the instance. """
    return securesystemslib.formats.encode_canonical(
        attr.asdict(self)).encode("UTF-8")
