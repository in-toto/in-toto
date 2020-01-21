import sys
import logging

# Increase timeout to accommodate tests on AppVeyor, which seems to have
# troubles finishing gpg operations within the securesystemslib default of 3s.
# NOTE: This must be done before importing in_toto, because in_toto
# transitively imports 'securesystemslib.process', which locks the default
# timeout arguments in its functions. Also note that this only works if in_toto
# tests are invoked as modules, e.g. via 'runtests.py' or 'python -m ...'.
# TODO: This needs to be fixed in securesystemslib
import securesystemslib.settings
securesystemslib.settings.SUBPROCESS_TIMEOUT = 100

import in_toto

class CapturableStreamHandler(logging.StreamHandler):
  """Override logging.StreamHandler's stream property to always write log
  output to `sys.stderr` available at the time of logging.
  """
  @property
  def stream(self):
    """Always use currently available sys.stderr. """
    return sys.stderr

  @stream.setter
  def stream(self, value):
    """Disable setting stream. """

# Python `unittest` is configured to buffer output to `sys.stdout/sys.stderr`
# (see `TextTestRunner` in `tests/runtests.py`) and only show it in case a test
# fails. Python `unittest` buffers output by overriding `sys.stdout/sys.stderr`
# before running tests, hence we need to log to that overridden `sys.stderr`,
# which we do by using a custom StreamHandler.
handler = CapturableStreamHandler()
# We also use a verbose logging level and format
formatter = logging.Formatter(in_toto.log.FORMAT_DEBUG)
handler.setFormatter(formatter)
in_toto.log.LOGGER.handlers = [handler]
in_toto.log.LOGGER.setLevel(logging.DEBUG)
