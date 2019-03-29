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

class TestCaseLib(unittest.TestCase):
  """TestCase subclass providing standard methods that will centrally
  integrate test script setup and teardown methods through overriding"""

  # Dummy artifact hashes
  sha256_foo = \
      "d65165279105ca6773180500688df4bdc69a2c7b771752f0a46ef120b7fd8ec3"
  sha256_foobar = \
      "155c693a6b7481f48626ebfc545f05236df679f0099225d6d0bc472e6dd21155"
  sha256_bar = \
      "cfdaaf1ab2e4661952a9dec5e8fa3c360c1b06b1a073e8493a7c46d2af8c504b"
  sha256_barfoo = \
      "2036784917e49b7685c7c17e03ddcae4a063979aa296ee5090b5bb8f8aeafc5d"
  sha256_foo_tar = \
      "93c3c35a039a6a3d53e81c5dbee4ebb684de57b7c8be11b8739fd35804a0e918"
  sha256_1 = \
      "d65165279105ca6773180500688df4bdc69a2c7b771752f0a46ef120b7fd8ec3"
  sha256_2 = \
      "cfdaaf1ab2e4661952a9dec5e8fa3c360c1b06b1a073e8493a7c46d2af8c504b"


  gnupg_home = None
  working_dir = os.getcwd()
  test_dir = os.path.realpath(tempfile.mkdtemp())

  key = {}
  key2 = None
  key_path = "test_key"
  key_path2 = "test-key2"
  need_second = False

  step_name = "test_step"
  link_name_unfinished = None
  artifact_exclude_orig = None
  artifact_base_path_orig = None

  need_key_pair = False
  extra_settings = None
  directory_str = None

  @classmethod
  def setUpClass(self):
    # Backup original cwd
    self.working_dir = os.getcwd()

    # Find demo files
    if self.extra_settings == "demo":
      demo_files = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "demo_files")

    # Create and change into temporary directory
    self.test_dir = os.path.realpath(tempfile.mkdtemp())
    os.chdir(self.test_dir)

    if self.need_key_pair:
      generate_and_write_rsa_keypair(self.key_path)
      self.key = prompt_import_rsa_key_from_file(self.key_path)
      if self.need_second:
        generate_and_write_rsa_keypair(self.key_path2)
        self.key2 = prompt_import_rsa_key_from_file(self.key_path2)
      if self.extra_settings == "link":
        self.link_name_unfinished = UNFINISHED_FILENAME_FORMAT.format(
            step_name=self.step_name, keyid=self.key["keyid"])
    elif self.extra_settings:
      if self.extra_settings == "keyrings":
        # Change into directory with gpg keychain
        self.gnupg_home = os.path.join(self.test_dir, self.directory_str)

        # Find keyrings
        gpg_keyring_path = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), "gpg_keyrings", self.directory_str)

        shutil.copytree(gpg_keyring_path, self.gnupg_home)
      elif self.extra_settings == "demo":
        # Copy demo files to temporary dir
        for file in os.listdir(demo_files):
          shutil.copy(os.path.join(demo_files, file), self.test_dir)

  @classmethod
  def tearDownClass(self, set_artifacts=False):
    """Change back to initial working dir and remove temp test directory. """
    os.chdir(self.working_dir)
    shutil.rmtree(self.test_dir)
    if set_artifacts:
      in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS = self.artifact_exclude_orig
      in_toto.settings.ARTIFACT_BASE_PATH = self.artifact_base_path_orig

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
