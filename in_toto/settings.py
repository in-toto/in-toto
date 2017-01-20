"""
<Program Name>
  settings.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  June 23, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  A global settings file used througout the entire package, inspired
  by Django's settings system.


<Pre-requisites>
  To make this work we use the simple-settings module available on Pypi.
  http://simple-settings.readthedocs.io/en/master/

  $ pip install simple-settings
  $ export SIMPLE_SETTINGS=toto.settings

  To access a settings:
  from simple_settings import settings

"""
import logging

# FIXME: Add as command line argument or to config file, e.g .in-toto-ignore
ARTIFACT_EXCLUDES=["*.link*", ".git", "*.pyc", "*~"]

# Debug level INFO shows a bunch of stuff that is happening
LOG_LEVEL = logging.INFO
# Debug level CRITICAL only shows in_toto-verify passing and failing
#LOG_LEVEL = logging.CRITICAL

# Used as base path for --materials and --products arguments when running
# in-toto-run/in-toto-record
# FIXME: This is likely to become a command line argument
# FIXME: Do we want different base paths for materials and products?
ARTIFACT_BASE_PATH = None
