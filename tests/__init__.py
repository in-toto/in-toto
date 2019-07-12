import sys
import logging
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
