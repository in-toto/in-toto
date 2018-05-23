#!/usr/bin/env python
"""
<Program Name>
  runtests.py

<Author>
  Santiago Torres <santiago@nyu.edu>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  May 23, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Script to search, load and run in-toto tests using the Python `unittest`
  framework.
"""

from unittest import defaultTestLoader, TextTestRunner
import sys
import os
import subprocess

def check_usable_gpg():
  """ Tries to execute gpg and figure out wether we can run tests that
      require gpg to be installed
  """
  try:
    subprocess.check_call(['gpg', '--version'])
  # sadly, this will through either a WindowsError or a FileNotFound error
  # so we need to catch a generic exception
  except Exception as e:
    os.environ["TEST_SKIP_GPG"] = "1"

# set the test prerrequisites (so far, we only check if gpg is installed)
check_usable_gpg()

suite = defaultTestLoader.discover(start_dir=".")
result = TextTestRunner(verbosity=2, buffer=True).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
