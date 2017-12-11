"""
<Program Name>
  log.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Oct 4, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Simple wrapper of Python's logger module.
"""

import logging
import in_toto.settings
import platform

RED = "\x1b[31m"
YELLOW = "\x1b[33m"
GREEN = "\x1b[32m"
MAGENTA = "\x1b[35m"
NO_COLOR = "\x1b[0m"

logging.basicConfig(level=in_toto.settings.LOG_LEVEL, format='%(message)s')

def color_encode(color, msg):
  """ Assigns ANSI escape codes to different log levels for colorized output """
  #FIXME: Add support for Windows (no support for ANSI escape codes)
  if platform.system().lower() is "windows" or not in_toto.settings.COLOR:
    return msg
  return "{}{}{}".format(color, msg, NO_COLOR)

def debug(msg):
  """ Verbose debugging """
  logging.debug("DEBUG: {}".format(color_encode(MAGENTA, msg)))

def info(msg):
  """Verbose user feedback. """
  logging.info("INFO: {}".format(color_encode(GREEN, msg)))

def warn(msg):
  """Verbose user warning. """
  logging.warn("WARNING: {}".format(color_encode(YELLOW, msg)))

def error(msg):
  """Prints unexpected errors """
  logging.error("ERROR: {}".format(color_encode(RED, msg)))

def pass_verification(msg):
  """Prints passing verification routines. """
  logging.critical("PASSING: {}".format(color_encode(GREEN, msg)))

def fail_verification(msg):
  """Prints failing verification. """
  logging.critical("FAILING: {}".format(color_encode(RED, msg)))
