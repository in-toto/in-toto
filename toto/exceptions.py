from toto.ssl_commons.exceptions import Error

class SignatureVerificationError(Error):
  """Indicates a signature verification Error. """
  pass

class LayoutExpiredError(Error):
  """Indicates that the layout expired. """
  pass

class RuleVerficationFailed(Error):
  """Indicates that a match rule verification failed. """
  pass