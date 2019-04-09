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
import tempfile
import shutil

import in_toto.settings
from in_toto.models.layout import Layout
from in_toto.util import (generate_and_write_rsa_keypair,
    prompt_import_rsa_key_from_file)
from in_toto.models.link import UNFINISHED_FILENAME_FORMAT

import unittest
from mock import patch

class SetupTestCase(unittest.TestCase):
  """TestCase subclass providing template superclass methods that centrally
  integrate test script setup and teardown through directory environment setup
  and flags which dictate execution of specialized code blocks.

  Supports setup for key pair generation, demo supply chain link metadata,
  key pair dummy material generation, and GPG keyring verification. Supports
  teardown of temporary test directories and artifact pattern settings.
  """
  @classmethod
  def setUpClass(self):
    # Backup original cwd
    self.working_dir = os.getcwd()

    # Create and change into temporary directory
    self.test_dir = os.path.realpath(tempfile.mkdtemp())
    os.chdir(self.test_dir)

  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp test directory. """
    os.chdir(self.working_dir)
    shutil.rmtree(self.test_dir)

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
      self.cli_main_func()

    self.assertEqual(raise_ctx.exception.code, status)
