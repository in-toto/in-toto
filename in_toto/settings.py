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
  A central place to define default settings that can be used throughout the
  package.

  Defaults can be changed,
   - here (hardcoded),
   - programmatically, e.g.
     ```
     import in_toto.settings
     in_toto.settings.ARTIFACT_BASE_PATH = "/home/user/project"
     ```
  - or, when using in-toto via command line tooling, with environment variables
    or RCfiles, see the `in_toto.user_settings` module

"""
import logging

# Debug level INFO shows a bunch of stuff that is happening
# FIXME: This setting currently can not be overridden with envvars or
# rcfiles, because that would involve additional evaluation of the parsed
# values. Let's ignore it for now and fix it with in-toto/in-toto#117
LOG_LEVEL = logging.INFO
# Debug level CRITICAL only shows in_toto-verify passing and failing
#LOG_LEVEL = logging.CRITICAL


# See docstring of `in-toto.record_artifacts_as_dict` for how this is used
ARTIFACT_EXCLUDE_PATTERNS = ["*.link*", ".git", "*.pyc", "*~"]

# Used as base path for --materials and --products arguments when running
# in-toto-run/in-toto-record
# If not set the current working directory is used as base path
# FIXME: Do we want different base paths for materials and products?
ARTIFACT_BASE_PATH = None
