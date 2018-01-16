from securesystemslib.exceptions import Error

class SignatureVerificationError(Error):
  """Indicates a signature verification Error. """
  pass

class LayoutExpiredError(Error):
  """Indicates that the layout expired. """
  pass

class RuleVerficationError(Error):
  """Indicates that artifact rule verification failed. """
  pass

class ThresholdVerificationError(Error):
  """Indicates that signature threshold verification failed. """
  pass

class BadReturnValueError(Error):
  """Indicates that a ran command exited with non-int or non-zero return
  value. """
  pass

class LinkNotFoundError(Error):
  """Indicates that a link file was not found. """
  pass

class SettingsError(Error):
  """Indicates an invalid setting. """
  pass
