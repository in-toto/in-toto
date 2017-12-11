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

logging.basicConfig(level=in_toto.settings.LOG_LEVEL, format='%(message)s')

def debug(msg):
  """ Verbose debugging """
  logging.debug("DEBUG: {}".format(in_toto.util.color_code(msg, 10)))

def info(msg):
  """Verbose user feedback. """
  logging.info("INFO: {}".format(in_toto.util.color_code(msg, 20)))

def warn(msg):
  """Verbose user warning. """
  logging.warn("WARNING: {}".format(in_toto.util.color_code(msg, 30)))

def error(msg):
  """Prints unexpected errors """
  logging.error("ERROR: {}".format(in_toto.util.color_code(msg, 40)))

def pass_verification(msg):
  """Prints passing verification routines. """
  logging.critical("PASSING: {}".format(in_toto.util.color_code(msg, 50)))

def fail_verification(msg):
  """Prints failing verification. """
  logging.critical("FAILING: {}".format(in_toto.util.color_code(msg, 50)))
