#!/usr/bin/env python
"""
<Program Name>
  common.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Feb 6, 2018

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Common code for in-toto unittests, import like so:
  `import tests.common`

  Tests importing this module, should be run from the project root, e.g.:
  `python tests/test_in_toto_run.py`
  or using the aggregator script (preferred way):
  `python tests/runtests.py`.

"""
import os
import sys
import inspect

import unittest
if sys.version_info >= (3, 3):
  from unittest.mock import patch # pylint: disable=no-name-in-module,import-error
else:
  from mock import patch # pylint: disable=import-error


def run_with_portable_scripts(decorated):

  print("patching...")
  scripts_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "scripts")
  print("scripts are located in {}".format(scripts_path))
  @patch.dict(os.environ, {"PATH": "{};{}".format(scripts_path, os.environ['PATH'])})
  class Patched(decorated):
    pass

  return Patched



class CliTestCase(unittest.TestCase):
  """TestCase subclass providing a test helper that patches sys.argv with
  passed arguments and asserts a SystemExit with a return code equal
  to the passed status argument.

  Subclasses of CliTestCase require a class variable that stores the main
  function of the cli tool to test as staticmethod, e.g.:

  ```
  import tests.common
  from in_toto.in_toto_run import main as in_toto_run_main

  class TestInTotoRunTool(tests.common.CliTestCase):
    cli_main_func = staticmethod(in_toto_run_main)
    ...

  ```
  """
  cli_main_func = None

  def __init__(self, *args, **kwargs):
    """Constructor that checks for the presence of a callable cli_main_func
    class variable. And stores the filename of the module containing that
    function, to be used as first argument when patching sys.argv in
    self.assert_cli_sys_exit.
    """
    if not callable(self.cli_main_func):
      raise Exception("Subclasses of `CliTestCase` need to assign the main"
          " function of the cli tool to test using `staticmethod()`: {}"
          .format(self.__class__.__name__))

    file_path = inspect.getmodule(self.cli_main_func).__file__
    self.file_name = os.path.basename(file_path)

    super(CliTestCase, self).__init__(*args, **kwargs)


  def assert_cli_sys_exit(self, cli_args, status):
    """Test helper to mock command line call and assert return value.
    The passed args does not need to contain the command line tool's name.
    This is assessed from  `self.cli_main_func`
    """
    with patch.object(sys, "argv", [self.file_name]
        + cli_args), self.assertRaises(SystemExit) as raise_ctx:
      self.cli_main_func() # pylint: disable=not-callable

    self.assertEqual(raise_ctx.exception.code, status)
