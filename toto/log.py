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
from simple_settings import settings

logging.basicConfig(level=settings.LOG_LEVEL, format='%(message)s')

def doing(msg):
  """Logs things that are currently being done """
  logging.info("DOING:   %s" % str(msg))

def warning(msg):
  """Logs things the user should be warned about """
  logging.warn("WARNING: %s" % str(msg))

def passing(msg):
  """Logs verification routines that pass """
  logging.critical("PASSING: %s" % str(msg))

def failing(msg):
  """Logs verification routines that fail """
  logging.critical("FAILING: %s" % str(msg))

def error(msg):
  """Logs program failures """
  logging.error("EXCEPTION: %s" % str(msg))
