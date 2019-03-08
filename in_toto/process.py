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
  - provide a special `run_duplicate_streams` function

"""
import os
import sys
import io
import tempfile
import logging
import time
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




def run_duplicate_streams(cmd, timeout=SUBPROCESS_TIMEOUT):
  """
  <Purpose>
    Provide a function that executes a command in a subprocess and returns its
    exit code and the contents of what it printed to its standard streams upon
    termination.

    NOTE: The function might behave unexpectedly with interactive commands.


  <Arguments>
    cmd:
            The command and its arguments. (list of str, or str)
            Splits a string specifying a command and its argument into a list
            of substrings, if necessary.

    timeout: (default see settings.SUBPROCESS_TIMEOUT)
            If the timeout expires, the child process will be killed and waited
            for and then subprocess.TimeoutExpired  will be raised.

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
    A tuple of command's exit code, standard output and standard error
    contents.

  """
  if isinstance(cmd, six.string_types):
    cmd = shlex.split(cmd)
  else:
    formats.LIST_OF_ANY_STRING_SCHEMA.check_match(cmd)

  # Use temporary files as targets for child process standard stream redirects
  # They seem to work better (i.e. do not hang) than pipes, when using
  # interactive commands like `vi`.
  stdout_fd, stdout_name = tempfile.mkstemp()
  stderr_fd, stderr_name = tempfile.mkstemp()
  try:
    with io.open(stdout_name, "r") as stdout_reader, \
        os.fdopen(stdout_fd, "w") as stdout_writer, \
        io.open(stderr_name, "r") as stderr_reader, \
        os.fdopen(stderr_fd, "w") as stderr_writer:

      # Start child , writing standard streams to temporary files
      proc = subprocess.Popen(cmd, stdout=stdout_writer,
          stderr=stderr_writer, universal_newlines=True)
      proc_start_time = time.time()

      stdout_str = stderr_str = ""
      stdout_part = stderr_part = ""

      # Read as long as the process runs or there is data on one of the streams
      while proc.poll() is None or stdout_part or stderr_part:

        # Raise timeout error in they same manner as `subprocess` would do it
        if (timeout is not None and
            time.time() > proc_start_time + timeout):
          proc.kill()
          proc.wait()
          raise subprocess.TimeoutExpired(cmd, timeout)

        # Read from child process's redirected streams, write to parent
        # process's standard streams and construct retuirn values
        stdout_part = stdout_reader.read()
        stderr_part = stderr_reader.read()
        sys.stdout.write(stdout_part)
        sys.stderr.write(stderr_part)
        sys.stdout.flush()
        sys.stderr.flush()
        stdout_str += stdout_part
        stderr_str += stderr_part

  finally:
    # The work is done or was interrupted, the temp files can be removed
    os.remove(stdout_name)
    os.remove(stderr_name)

  # Return process exit code and captured stream
  return proc.poll(), stdout_str, stderr_str
