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
import in_toto.process


class Test_Process(unittest.TestCase):
  """Test subprocess interface. """

  def test_input_vs_stdin(self):
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


if __name__ == "__main__":
  unittest.main()
