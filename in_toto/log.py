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

def doing(msg):
  """Logs things that are currently being done """
  logging.info("DOING:   {}".format(msg))

def warning(msg):
  """Logs things the user should be warned about """
  logging.warn("WARNING: {}".format(msg))

def passing(msg):
  """Logs verification routines that pass """
  logging.critical("PASSING: {}".format(msg))

def failing(msg):
  """Logs verification routines that fail """
  logging.critical("FAILING: {}".format(msg))

def error(msg):
  """Logs program failures """
  logging.error("EXCEPTION: {}".format(msg))
