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
  import subprocess32 as subprocess # pragma: no cover
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
def run(cmd, check=True, _input=None, stdin=None, stdout=None, stderr=None,
        timeout=SUBPROCESS_TIMEOUT, universal_newlines=False):
  """
  <Purpose>
    Run the specified command, WITHOUT writing to standard input, and WITHOUT
    writing to standard output and error.  Note that we do NOT check whether
    the command returned a non-zero code.

  <Arguments>
    cmd:
            The command and its arguments. (list of str, or str)
            Splits a string specifying a command and its argument into a list
            of substrings, if necessary.

    check:
            "If check is true, and the process exits with a non-zero exit code,
            a CalledProcessError exception will be raised. Attributes of that
            exception hold the arguments, the exit code, and stdout and stderr
            if they were captured."

    _input:
            "The input argument is passed to Popen.communicate() and thus to
            the subprocess's stdin. If used it must be a byte sequence, or a
            string if universal_newlines=True. When used, the internal Popen
            object is automatically created with stdin=PIPE, and the stdin
            argument may not be used as well."

    stdin, stdout, stderr:
            "stdin, stdout and stderr specify the executed program's standard
            input, standard output and standard error file handles,
            respectively. Valid values are PIPE, DEVNULL, an existing file
            descriptor (a positive integer), an existing file object, and None.
            PIPE indicates that a new pipe to the child should be created.
            DEVNULL indicates that the special file os.devnull will be used.
            With the default settings of None, no redirection will occur; the
            child's file handles will be inherited from the parent.
            Additionally, stderr can be STDOUT, which indicates that the stderr
            data from the applications should be captured into the same file
            handle as for stdout."

    timeout:
            "The timeout argument is passed to Popen.communicate(). If the
            timeout expires, the child process will be killed and waited for.
            The TimeoutExpired exception will be re-raised after the child
            process has terminated."

    universal_newlines:
            "If universal_newlines is False the file objects stdin, stdout and
            stderr will be opened as binary streams, and no line ending
            conversion is done."

            "If universal_newlines is True, these file objects will be opened
            as text streams in universal newlines mode using the encoding
            returned by locale.getpreferredencoding(False). For stdin, line
            ending characters '\n' in the input will be converted to the
            default line separator os.linesep. For stdout and stderr, all line
            endings in the output will be converted to '\n'. For more
            information see the documentation of the io.TextIOWrapper class
            when the newline argument to its constructor is None."

  <Exceptions>
    securesystemslib.exceptions.FormatError:
            If the cmd as list does not match
            in_toto.formats.LIST_OF_ANY_STRING_SCHEMA.

    OSError:
            If the given command is not present or non-executable.

    subprocess.TimeoutExpired:
            If the process does not terminate after timeout seconds.

  <Side Effects>
    The side effects of executing the given command in this environment.

  <Returns>
    A subprocess.CompletedProcess instance.

  """
  if isinstance(cmd, six.string_types):
    cmd = shlex.split(cmd)
  else:
    formats.LIST_OF_ANY_STRING_SCHEMA.check_match(cmd)

  # The reason why we are not allowed to even specify stdin=None when input
  # is specified is due to this overly stringent code in subprocess:
  # https://github.com/google/python-subprocess32/blob/560f1a92db18c2d2bebe4049756528ce827aa366/subprocess32.py#L402
  if _input:
    log.debug('Ignoring stdin: '+str(stdin))
    return subprocess.run(cmd, check=check, input=_input,
      stdout=stdout, stderr=stderr, timeout=timeout,
      universal_newlines=universal_newlines)
  else:
    log.debug('Ignoring input: '+str(input))
    return subprocess.run(cmd, check=check, stdin=stdin,
      stdout=stdout, stderr=stderr, timeout=timeout,
      universal_newlines=universal_newlines)


