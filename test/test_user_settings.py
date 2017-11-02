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
  Test in-toto.user_settings.py

"""

import os
import sys
import unittest
import logging
import shutil
import tempfile
import in_toto.settings
import in_toto.user_settings

# Suppress all the user feedback that we print using a base logger
logging.getLogger().setLevel(logging.CRITICAL)

class TestUserSettings(unittest.TestCase):
  @classmethod
  def setUpClass(self):
    self.working_dir = os.getcwd()

    # We use `demo_files` as test dir because it has an `.in_totorc`, which
    # we is loaded (from CWD) in `user_settings.set_settings` related tests
    self.test_dir = os.path.join(os.path.dirname(__file__), "demo_files")
    os.chdir(self.test_dir)

    # Backup settings
    self.settings_backup = {}
    for key in dir(in_toto.settings):
      self.settings_backup[key] = getattr(in_toto.settings, key)

    os.environ["IN_TOTO_ARTIFACT_EXCLUDES"] = "e:n:v"
    os.environ["IN_TOTO_artifact_base_path"] = "e/n/v"
    os.environ["IN_TOTO_NEW_ENV_SETTING"] = "new env setting"
    os.environ["NOT_IN_TOTO_NOTHING"] = "nothing"


  @classmethod
  def tearDownClass(self):
    os.chdir(self.working_dir)

    # Restore settings, other unittests might depend on defaults
    for key, val in self.settings_backup.iteritems():
      setattr(in_toto.settings, key, val)


  def test_get_rc(self):
    """ Test rcfile parsing in CWD. """
    rc_dict = in_toto.user_settings.get_rc()
    self.assertEquals(rc_dict["ARTIFACT_BASE_PATH"], "r/c/file")
    self.assertListEqual(rc_dict["ARTIFACT_EXCLUDES"], ["r", "c", "file"])
    self.assertEquals(rc_dict["NEW_RC_SETTING"], "new rc setting")


  def test_get_env(self):
    """ Test environment variables parsing, prefix and colon splitting. """
    env_dict = in_toto.user_settings.get_env()
    self.assertEquals(env_dict["ARTIFACT_BASE_PATH"], "e/n/v")
    self.assertListEqual(env_dict["ARTIFACT_EXCLUDES"], ["e", "n", "v"])
    self.assertEquals(env_dict["NEW_ENV_SETTING"], "new env setting")
    self.assertFalse("NOT_IN_TOTO_NOTHING" in env_dict)


  def test_set_settings(self):
    """ Test precedence of rc over env and whitelisting. """
    in_toto.user_settings.set_settings()

    # RCfile settings have precedence over env settings
    self.assertEquals(in_toto.settings.ARTIFACT_BASE_PATH, "r/c/file")
    self.assertListEqual(in_toto.settings.ARTIFACT_EXCLUDES, ["r", "c", "file"])

    # Not whitelisted items are returned by get_rc but ignored by set_settings
    self.assertTrue("NEW_RC_SETTING" in in_toto.user_settings.get_rc())
    self.assertRaises(AttributeError, getattr, in_toto.settings,
        "NEW_RC_SETTING")

    # Not whitelisted items are returned by get_env but ignored by set_settings
    self.assertTrue("NEW_ENV_SETTING" in in_toto.user_settings.get_env())
    self.assertRaises(AttributeError, getattr, in_toto.settings,
        "NEW_ENV_SETTING")

if __name__ == "__main__":
  unittest.main()
