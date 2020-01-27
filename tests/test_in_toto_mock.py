#!/usr/bin/env python
"""
<Program Name>
  test_in_toto_mock.py

<Author>
  Shikher Verma <root@shikherverma.com>

<Started>
  June 12, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test in_toto_mock command line tool.

"""
import os
import unittest
import logging

from in_toto.in_toto_mock import main as in_toto_mock_main

from tests.common import CliTestCase, TmpDirMixin

# Required to cache and restore default log level
logger = logging.getLogger("in_toto")


class TestInTotoMockTool(CliTestCase, TmpDirMixin):
  """Test in_toto_mock's main() - requires sys.argv patching; and
  in_toto_mock- calls runlib and error logs/exits on Exception. """
  cli_main_func = staticmethod(in_toto_mock_main)

  @classmethod
  def setUpClass(self):
    """Create and change into temporary directory,
    dummy artifact and base arguments. """
    self.set_up_test_dir()

    # Below tests override the base logger ('in_toto') log level to
    # `logging.INFO`. We cache the original log level before running the tests
    # to restore it afterwards.
    self._base_log_level = logger.level

    self.test_step = "test_step"
    self.test_link = self.test_step + ".link"
    self.test_artifact = "test_artifact"
    open(self.test_artifact, "w").close()


  @classmethod
  def tearDownClass(self):
    self.tear_down_test_dir()

    # Restore log level to what it was before running in-toto-mock
    logger.setLevel(self._base_log_level)


  def tearDown(self):
    try:
      os.remove(self.test_link)
    except OSError:
      pass


  def test_main_required_args(self):
    """Test CLI command with required arguments. """

    args = ["--name", self.test_step, "--", "python", "--version"]
    self.assert_cli_sys_exit(args, 0)

    self.assertTrue(os.path.exists(self.test_link))


  def test_main_wrong_args(self):
    """Test CLI command with missing arguments. """

    wrong_args_list = [
      [],
      ["--name", "test-step"],
      ["--", "echo", "blub"]]

    for wrong_args in wrong_args_list:
      self.assert_cli_sys_exit(wrong_args, 2)
      self.assertFalse(os.path.exists(self.test_link))


  def test_main_bad_cmd(self):
    """Test CLI command with non-existing command. """
    # TODO: Is it safe to assume this command does not exist, or should we
    # assert for it?
    args = ["-n", "bad-command", "--", "ggadsfljasdhlasdfljvzxc"]
    self.assert_cli_sys_exit(args, 1)


if __name__ == "__main__":
  unittest.main()
