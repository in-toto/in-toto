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

def info(msg):
  """Verbose user feedback. """
  logging.info("%s", msg)

def warn(msg):
  """Verbose user warning. """
  logging.warn("WARNING: %s", msg)

def error(msg):
  """Prints unexpected errors """
  logging.error("ERROR: %s", msg)

def pass_verification(msg):
  """Prints passing verification routines. """
  logging.critical("PASSING: %s", msg)

def fail_verification(msg):
  """Prints failing verification. """
  logging.critical("FAILING: %s", msg)
