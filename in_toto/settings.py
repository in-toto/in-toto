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
  Mostly for things that will eventually be moved to
  separate configuration files or command line arguments.

  Note:
  This used to be a global settings file for in_toto and its submodules using
  `simple_settings`. Since submodules were removed `simple_settings` is no
  longer needed.

  The former submodule and now external dependency `securesystemslib` has its
  own settings file, that should henceforth be used programmatically.

  E.g.:
  ```
  import securesystemslib.settings
  securesystemslib.settings.RSA_CRYPTO_LIBRARY = "pyca-cryptography" # default
  ```

"""
import logging

# Debug level INFO shows a bunch of stuff that is happening
LOG_LEVEL = logging.INFO
# Debug level CRITICAL only shows in_toto-verify passing and failing
#LOG_LEVEL = logging.CRITICAL

# FIXME: Add as command line argument or to config file, e.g .in-toto-ignore
ARTIFACT_EXCLUDES = ["*.link*", ".git", "*.pyc", "*~"]

# Used as base path for --materials and --products arguments when running
# in-toto-run/in-toto-record
# FIXME: This is likely to become a command line argument
# FIXME: Do we want different base paths for materials and products?
ARTIFACT_BASE_PATH = None
