#!/usr/bin/env python
"""
<Program Name>
  test_process.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Oct 4, 2018

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test subprocess interface.

"""
import os
import tempfile
import unittest
import shlex
import io
import sys
import in_toto.process


class Test_Process(unittest.TestCase):
  """Test subprocess interface. """

  def test_run_input_vs_stdin(self):
    """Test that stdin kwarg is only used if input kwarg is not supplied. """

    # Create a temporary file, passed as `stdin` argument
    fd, path = tempfile.mkstemp(text=True)
    os.write(fd, b"use stdin kwarg")
    os.close(fd)

    stdin_file = open(path)
    cmd = \
        "python -c \"import sys; assert(sys.stdin.read() == '{}')\""

    # input is used in favor of stdin
    in_toto.process.run(cmd.format("use input kwarg"),
        input=b"use input kwarg",
        stdin=stdin_file)

    # stdin is only used if input is not supplied
    in_toto.process.run(cmd.format("use stdin kwarg"), stdin=stdin_file)

    # Clean up
    stdin_file.close()
    os.remove(path)


  def test_run_duplicate_streams(self):
    """Test output as streams and as returned.  """
    # Command that prints 'foo' to stdout and 'bar' to stderr.
    cmd = ("python -c \""
        "import sys;"
        "sys.stdout.write('foo');"
        "sys.stderr.write('bar');\"")

    # Create and open fake targets for standard streams
    stdout_fd, stdout_fn = tempfile.mkstemp()
    stderr_fd, stderr_fn = tempfile.mkstemp()
    with io.open(stdout_fn, "r") as fake_stdout_reader, \
        os.fdopen(stdout_fd, "w") as fake_stdout_writer, \
        io.open(stderr_fn, "r") as fake_stderr_reader, \
        os.fdopen(stderr_fd, "w") as fake_stderr_writer:

      # Backup original standard streams and redirect to fake targets
      real_stdout = sys.stdout
      real_stderr = sys.stderr
      sys.stdout = fake_stdout_writer
      sys.stderr = fake_stderr_writer

      # Run command
      ret_code, ret_stdout, ret_stderr = \
          in_toto.process.run_duplicate_streams(cmd)

      # Rewind fake standard streams
      fake_stdout_reader.seek(0)
      fake_stderr_reader.seek(0)

      # Assert that what was printed and what was returned is correct
      self.assertTrue(ret_stdout == fake_stdout_reader.read() == "foo")
      self.assertTrue(ret_stderr == fake_stderr_reader.read() == "bar")
      # Also assert the default return value
      self.assertEqual(ret_code, 0)

      # Reset original streams
      sys.stdout = real_stdout
      sys.stderr = real_stderr

    # Remove fake standard streams
    os.remove(stdout_fn)
    os.remove(stderr_fn)


  def test_run_duplicate_streams_arg_return_code(self):
    """Test command arg as string and list and return code. """
    cmd_str = ("python -c \""
        "import sys;"
        "sys.exit(100)\"")
    cmd_list = shlex.split(cmd_str)

    for cmd in [cmd_str, cmd_list]:
      return_code, _, _ = in_toto.process.run_duplicate_streams(cmd)
      self.assertEqual(return_code, 100)


  def test_run_duplicate_streams_timeout(self):
    """Test raise TimeoutExpired. """
    with self.assertRaises(in_toto.process.subprocess.TimeoutExpired):
      in_toto.process.run_duplicate_streams("python --version", timeout=-1)



if __name__ == "__main__":
  unittest.main()
