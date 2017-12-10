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

logging.basicConfig(level=in_toto.settings.LOG_LEVEL, format='%(message)s')

def debug(msg):
  """ Verbose debugging """
  logging.debug("DEBUG: {}".format(color_code(msg, 10)))

def info(msg):
  """Verbose user feedback. """
  logging.info("INFO: {}".format(color_code(msg, 20)))

def warn(msg):
  """Verbose user warning. """
  logging.warn("WARNING: {}".format(color_code(msg, 30)))

def error(msg):
  """Prints unexpected errors """
  logging.error("ERROR: {}".format(color_code(msg, 40)))

def pass_verification(msg):
  """Prints passing verification routines. """
  logging.critical("PASSING: {}".format(color_code(msg, 50)))

def fail_verification(msg):
  """Prints failing verification. """
  logging.critical("FAILING: {}".format(color_code(msg, 50)))

def color_code(msg, lvl):
  """ Colorizing output for operating systems that support ANSI codes """
  if in_toto.settings.COLOR:
    level = logging.getLevelName(lvl)
    levelGenerator = { "CRITICAL" : "\x1b[31m", # red
                       "ERROR" : "\x1b[31m", #  red
                       "WARNING" : "\x1b[33m", # yellow
                       "INFO" : "\x1b[32m",  # green
                       "DEBUG" : "\x1b[35m" } # magenta 
    #FIXME: Add support for Windows OS (Windows has no support for ANSI codes)
    if platform.system().lower() is not "windows":
      for key, value in levelGenerator.iteritems():
        if level in key:
          return "{}{}\x1b[0m".format(value, msg)
  return msg