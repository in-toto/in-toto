#!/usr/bin/env python
"""
<Program Name>
  process.py

<Author>
  Trishank Karthik Kuppusamy <trishank.kuppusamy@datadoghq.com>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  September 25, 2018

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provide a common interface for Python's subprocess module to:

  - require the Py3 subprocess backport `subprocess32` on Python2,
  - in-toto namespace subprocess constants (DEVNULL, PIPE) and
  - provide a custom `subprocess.run` wrapper

"""
import logging
import shlex

import six

if six.PY2:
  import subprocess32 as subprocess # pragma: no cover pylint: disable=import-error
else: # pragma: no cover
  import subprocess

import in_toto.formats as formats


# Constants.
from in_toto.settings import SUBPROCESS_TIMEOUT
DEVNULL = subprocess.DEVNULL
PIPE = subprocess.PIPE


# Inherits from in_toto base logger (c.f. in_toto.log)
log = logging.getLogger(__name__)


# TODO: Properly duplicate standard streams (issue #11)
def run(cmd, check=True, timeout=SUBPROCESS_TIMEOUT, **kwargs):
  """
  <Purpose>
    Provide wrapper for `subprocess.run` (see
    https://github.com/python/cpython/blob/3.5/Lib/subprocess.py#L352-L399)
    where:

    * `timeout` has a default (see in_toto.settings.SUBPROCESS_TIMEOUT),
    * `check` is `True` by default,
    * there is only one positional argument, i.e. `cmd` that can be either
      a str (will be split with shlex) or a list of str and
    * instead of raising a ValueError if both `input` and `stdin` are passed,
      `stdin` is ignored.


  <Arguments>
    cmd:
            The command and its arguments. (list of str, or str)
            Splits a string specifying a command and its argument into a list
            of substrings, if necessary.

    check: (default True)
            "If check is true, and the process exits with a non-zero exit code,
            a CalledProcessError exception will be raised. Attributes of that
            exception hold the arguments, the exit code, and stdout and stderr
            if they were captured."

    timeout: (default see settings.SUBPROCESS_TIMEOUT)
            "The timeout argument is passed to Popen.communicate(). If the
            timeout expires, the child process will be killed and waited for.
            The TimeoutExpired exception will be re-raised after the child
            process has terminated."

    **kwargs:
            See subprocess.run and Frequently Used Arguments to Popen
            constructor for available kwargs.
            https://docs.python.org/3.5/library/subprocess.html#subprocess.run
            https://docs.python.org/3.5/library/subprocess.html#frequently-used-arguments

  <Exceptions>
    securesystemslib.exceptions.FormatError:
            If the `cmd` is a list and does not match
            in_toto.formats.LIST_OF_ANY_STRING_SCHEMA.

    OSError:
            If the given command is not present or non-executable.

    subprocess.TimeoutExpired:
            If the process does not terminate after timeout seconds. Default
            is `settings.SUBPROCESS_TIMEOUT`

  <Side Effects>
    The side effects of executing the given command in this environment.

  <Returns>
    A subprocess.CompletedProcess instance.

  """
  # Make list of command passed as string for convenience
  if isinstance(cmd, six.string_types):
    cmd = shlex.split(cmd)
  else:
    formats.LIST_OF_ANY_STRING_SCHEMA.check_match(cmd)

  # NOTE: The CPython implementation would raise a ValueError here, we just
  # don't pass on `stdin` if the user passes `input` and `stdin`
  # https://github.com/python/cpython/blob/3.5/Lib/subprocess.py#L378-L381
  if kwargs.get("input") is not None and "stdin" in kwargs:
    log.debug("stdin and input arguments may not both be used. "
        "Ignoring passed stdin: " + str(kwargs["stdin"]))
    del kwargs["stdin"]

  return subprocess.run(cmd, check=check, timeout=timeout, **kwargs)
