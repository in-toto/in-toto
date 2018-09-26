import os
import logging
import shlex
import sys

import six

if os.name == 'posix' and sys.version_info[0] < 3:
  import subprocess32 as subprocess # pragma: no cover
else: # pragma: no cover
  import subprocess

import in_toto.formats as formats

from in_toto.settings import SUBPROCESS_TIMEOUT


# Inherits from in_toto base logger (c.f. in_toto.log)
log = logging.getLogger(__name__)


def shlex_split(cmd):
  """
  <Purpose>
    Splits a string specifying a command and its argument into a list of
    substrings, if necessary.

  <Arguments>
    cmd:
            The command and its arguments. (str | list)

  <Exceptions>
    securesystemslib.exceptions.FormatError:
            If the cmd as list does not match
            in_toto.formats.LIST_OF_ANY_STRING_SCHEMA.

  <Side Effects>
    None.

  <Returns>
    A list of strings matching in_toto.formats.LIST_OF_ANY_STRING_SCHEMA.

  """
  if isinstance(cmd, six.string_types):
    cmd = shlex.split(cmd)
  else:
    formats.LIST_OF_ANY_STRING_SCHEMA.check_match(cmd)
  return cmd


# TODO: Properly duplicate standard streams (issue #11)
def run_pipe_stdout_pipe_stderr(cmd):
  """
  <Purpose>
    Run the specified command, WITHOUT writing to standard input, and WITHOUT
    writing to standard output and error.  Note that we do NOT check whether
    the command returned a non-zero code.

  <Arguments>
    cmd:
            The command and its arguments. (list of str)

  <Exceptions>
    OSError:
            If the given command is not present or non-executable.

    subprocess.TimeoutExpired:
            If the process does not terminate after timeout seconds.

  <Side Effects>
    The side effects of executing the given command in this environment.

  <Returns>
    A subprocess.CompletedProcess instance.

  """
  cmd = shlex_split(cmd)
  return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    universal_newlines=True, timeout=SUBPROCESS_TIMEOUT)


def run_no_stdout_no_stderr(cmd):
  """
  <Purpose>
    Run the specified command, WITHOUT writing to standard input, output, and
    error.  Note that we do NOT check whether the command returned a non-zero
    code.

  <Arguments>
    cmd:
            The command and its arguments. (list of str)

  <Exceptions>
    OSError:
            If the given command is not present or non-executable.

    subprocess.TimeoutExpired:
            If the process does not terminate after timeout seconds.

  <Side Effects>
    The side effects of executing the given command in this environment.

  <Returns>
    A subprocess.CompletedProcess instance.

  """
  cmd = shlex_split(cmd)
  return subprocess.run(cmd, stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL, timeout=SUBPROCESS_TIMEOUT)


def check_call_no_stdout_no_stderr(cmd):
  """
  <Purpose>
    Run the specified command, WITHOUT writing to standard input, output, and
    error.  However, note that we DO check whether the command returned a
    non-zero code.

  <Arguments>
    cmd:
            The command and its arguments. (list of str)

  <Exceptions>
    OSError:
            If the given command is not present or non-executable.

    subprocess.TimeoutExpired:
            If the process does not terminate after timeout seconds.

  <Side Effects>
    The side effects of executing the given command in this environment.

  <Returns>
    A subprocess.CompletedProcess instance.

  """
  cmd = shlex_split(cmd)
  return subprocess.check_call(cmd, stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL, timeout=SUBPROCESS_TIMEOUT)


def check_call_write_stdin_pipe_stdout(cmd, content, universal_newlines=False):
  """
  <Purpose>
    Run the specified command, WITH writing the given input to standard input,
    WITH writing to standard output, and WITHOUT writing to standard error.
    Note that we DO check whether the command returned a non-zero code.

  <Arguments>
    cmd:
            The command and its arguments. (list of str)

    content:
            The content to write to the process stdin. (bytes if
            universal_newlines=False, otherwise str)

    universal_newlines:
            If False, then the given input must be encoded as bytes; otherwise,
            as a string.

  <Exceptions>
    OSError:
            If the given command is not present or non-executable.

    subprocess.TimeoutExpired:
            If the process does not terminate after timeout seconds.

  <Side Effects>
    The side effects of executing the given command in this environment.

  <Returns>
    A subprocess.CompletedProcess instance.

  """
  cmd = shlex_split(cmd)
  return subprocess.run(cmd, input=content, stdout=subprocess.PIPE,
      stderr=subprocess.DEVNULL, timeout=SUBPROCESS_TIMEOUT,
      universal_newlines=universal_newlines, check=True)


def check_output_no_stdin_no_stderr(cmd, universal_newlines=False):
  """
  <Purpose>
    Run the specified command, WITHOUT writing to standard input, output, and
    error. However, we DO extract the output of the command. Also, note that we
    DO check whether the command returned a non-zero code.

  <Arguments>
    cmd:
            The command and its arguments. (list of str)

    universal_newlines:
            If False, then the output is encoded as bytes; otherwise, as a
            string.

  <Exceptions>
    OSError:
            If the given command is not present or non-executable.

    subprocess.TimeoutExpired:
            If the process does not terminate after timeout seconds.

  <Side Effects>
    The side effects of executing the given command in this environment.

  <Returns>
    A subprocess.CompletedProcess instance.

  """
  cmd = shlex_split(cmd)
  return subprocess.check_output(cmd, stderr=subprocess.DEVNULL,
    timeout=SUBPROCESS_TIMEOUT, universal_newlines=universal_newlines)


