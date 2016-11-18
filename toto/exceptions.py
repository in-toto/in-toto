from toto.ssl_commons.exceptions import Error

class CommandAlignmentFailed(Error):
  """Indicates that Command Alignment failed. """
  pass

class RuleVerficationFailed(Error):
  """Indicates that a match rule verification failed. """
  pass

