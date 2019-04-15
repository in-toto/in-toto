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
  """Set `TEST_SKIP_GPG` environment variable if neither gpg2 nor gpg is
  available.

  """
  os.environ["TEST_SKIP_GPG"] = "1"
  for gpg in ["gpg2", "gpg"]:
    try:
      subprocess.check_call([gpg, "--version"])

    except OSError:
      pass

    else:
      # If one of the two exists, we can unset the skip envvar and ...
      os.environ.pop("TEST_SKIP_GPG", None)
      # ... abort the availability check.:
      break

check_usable_gpg()

suite = defaultTestLoader.discover(start_dir=".")
result = TextTestRunner(verbosity=2, buffer=True).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
