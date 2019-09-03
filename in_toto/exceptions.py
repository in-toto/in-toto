# TODO: Add module docstring and remove pylint exemption in in-toto/in-toto#126
# pylint: disable=missing-docstring
from securesystemslib.exceptions import Error

class SignatureVerificationError(Error):
  """Indicates a signature verification Error. """

class LayoutExpiredError(Error):
  """Indicates that the layout expired. """

class RuleVerificationError(Error):
  """Indicates that artifact rule verification failed. """

class ThresholdVerificationError(Error):
  """Indicates that signature threshold verification failed. """

class BadReturnValueError(Error):
  """Indicates that a ran command exited with non-int or non-zero return
  value. """

class LinkNotFoundError(Error):
  """Indicates that a link file was not found. """

class UnsupportedKeyTypeError(Error):
  """Indicates that the specified key type is not yet supported. """

class PrefixError(Error):
  """Indicates that there is an error because of the prefixes passed. """
