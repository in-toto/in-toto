from securesystemslib.exceptions import Error

class SignatureVerificationError(Error):
  """Indicates a signature verification Error. """
  pass

class LayoutExpiredError(Error):
  """Indicates that the layout expired. """
  pass

class RuleVerficationError(Error):
  """Indicates that a match rule verification failed. """
  pass

class BadReturnValueError(Error):
  """Indicates that a ran command exited with non-int or non-zero return
  value. """
