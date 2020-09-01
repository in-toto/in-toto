"""
<Program Name>
  test_user_settings.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Oct 26, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test in_toto/user_settings.py

"""
import six

import os
import unittest
import in_toto.settings
import in_toto.user_settings


class TestUserSettings(unittest.TestCase):
  @classmethod
  def setUpClass(self):
    self.working_dir = os.getcwd()

    # Backup settings to restore them in `tearDownClass`
    self.settings_backup = {}
    for key in dir(in_toto.settings):
      self.settings_backup[key] = getattr(in_toto.settings, key)

    # We use `rc_test` as test dir because it has an `.in_totorc`, which
    # is loaded (from CWD) in `user_settings.set_settings` related tests
    self.test_dir = os.path.join(os.path.dirname(__file__), "rc_test")
    os.chdir(self.test_dir)

    os.environ["IN_TOTO_ARTIFACT_EXCLUDE_PATTERNS"] = "e:n:v"
    os.environ["IN_TOTO_ARTIFACT_BASE_PATH"] = "e/n/v"
    os.environ["IN_TOTO_LINK_CMD_EXEC_TIMEOUT"] = "0.1"
    os.environ["IN_TOTO_NOT_WHITELISTED"] = "parsed"
    os.environ["NOT_PARSED"] = "ignored"


  @classmethod
  def tearDownClass(self):
    os.chdir(self.working_dir)

    # Other unittests might depend on defaults:
    # Restore monkey patched settings ...
    for key, val in six.iteritems(self.settings_backup):
      setattr(in_toto.settings, key, val)

    # ... and delete test environment variables
    del os.environ["IN_TOTO_ARTIFACT_EXCLUDE_PATTERNS"]
    del os.environ["IN_TOTO_ARTIFACT_BASE_PATH"]
    del os.environ["IN_TOTO_LINK_CMD_EXEC_TIMEOUT"]
    del os.environ["IN_TOTO_NOT_WHITELISTED"]
    del os.environ["NOT_PARSED"]


  def test_get_rc(self):
    """ Test rcfile parsing in CWD. """
    rc_dict = in_toto.user_settings.get_rc()

    # Parsed (and split) and used by `set_settings` to monkeypatch settings
    self.assertListEqual(rc_dict["ARTIFACT_EXCLUDE_PATTERNS"], ["r", "c", "file"])
    self.assertEqual(rc_dict["LINK_CMD_EXEC_TIMEOUT"], "20")

    # Parsed but ignored in `set_settings` (not in case sensitive whitelist)
    self.assertEqual(rc_dict["artifact_base_path"], "r/c/file")
    self.assertEqual(rc_dict["new_rc_setting"], "new rc setting")


  def test_get_env(self):
    """ Test environment variables parsing, prefix and colon splitting. """
    env_dict = in_toto.user_settings.get_env()

    # Parsed and used by `set_settings` to monkeypatch settings
    self.assertEqual(env_dict["ARTIFACT_BASE_PATH"], "e/n/v")

    # Parsed (and split) but overriden by rcfile setting in `set_settings`
    self.assertListEqual(env_dict["ARTIFACT_EXCLUDE_PATTERNS"],
        ["e", "n", "v"])

    # Parsed and used by `set_settings`
    self.assertEqual(env_dict["LINK_CMD_EXEC_TIMEOUT"], "0.1")

    # Parsed but ignored in `set_settings` (not in case sensitive whitelist)
    self.assertEqual(env_dict["NOT_WHITELISTED"], "parsed")

    # Not parsed because of missing prefix
    self.assertFalse("NOT_PARSED" in env_dict)


  def test_set_settings(self):
    """ Test precedence of rc over env and whitelisting. """
    in_toto.user_settings.set_settings()

    # From envvar IN_TOTO_ARTIFACT_BASE_PATH
    self.assertEqual(in_toto.settings.ARTIFACT_BASE_PATH, "e/n/v")

    # From RCfile setting (has precedence over envvar setting)
    self.assertListEqual(in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS,
        ["r", "c", "file"])
    self.assertEqual(in_toto.settings.LINK_CMD_EXEC_TIMEOUT, "20")

    # Not whitelisted rcfile settings are ignored by `set_settings`
    self.assertTrue("new_rc_setting" in in_toto.user_settings.get_rc())
    self.assertRaises(AttributeError, getattr, in_toto.settings,
        "NEW_RC_SETTING")

    # Not whitelisted envvars are ignored by `set_settings`
    self.assertTrue("NOT_WHITELISTED" in in_toto.user_settings.get_env())
    self.assertRaises(AttributeError, getattr, in_toto.settings,
        "NOT_WHITELISTED")

if __name__ == "__main__":
  unittest.main()
