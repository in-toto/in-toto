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
  Test user settings module.

"""

import os
import sys
import unittest
import logging
import shutil
import tempfile
import in_toto.settings
import in_toto.user_settings

WORKING_DIR = os.getcwd()

# Suppress all the user feedback that we print using a base logger
logging.getLogger().setLevel(logging.CRITICAL)

class TestUserSettings(unittest.TestCase):
  @classmethod
  def setUpClass(self):
    self.working_dir = os.getcwd()
    self.test_dir = os.path.realpath(tempfile.mkdtemp())
    os.chdir(self.test_dir)

    # Backup settings
    self.settings_backup = {}
    for key in dir(in_toto.settings):
      self.settings_backup[key] = getattr(in_toto.settings, key)

    # Create an rc file and set some environment variables
    with open(".in_totorc", "w") as fobj:
      fobj.write(
          "[settings]\n"
          "artifact_basepath=r/c/file\n"
          "ARTIFACT_EXCLUDES=r:c:file\n"
          "new_rc_setting=new rc setting")

    os.environ["IN_TOTO_ARTIFACT_EXCLUDES"] = "e:n:v"
    os.environ["IN_TOTO_artifact_basepath"] = "e/n/v"
    os.environ["IN_TOTO_NEW_ENV_SETTING"] = "new env setting"
    os.environ["NOT_IN_TOTO_NOTHING"] = "nothing"


  @classmethod
  def tearDownClass(self):
    os.chdir(self.working_dir)
    shutil.rmtree(self.test_dir)

    # Restore settings, other unittests might depend on defaults
    for key, val in self.settings_backup.iteritems():
      setattr(in_toto.settings, key, val)


  def test_get_rc(self):
    rc_dict = in_toto.user_settings.get_rc()
    self.assertEquals(rc_dict["ARTIFACT_BASEPATH"], "r/c/file")
    self.assertListEqual(rc_dict["ARTIFACT_EXCLUDES"], ["r", "c", "file"])
    self.assertEquals(rc_dict["NEW_RC_SETTING"], "new rc setting")


  def test_get_env(self):
    env_dict = in_toto.user_settings.get_env()
    self.assertEquals(env_dict["ARTIFACT_BASEPATH"], "e/n/v")
    self.assertListEqual(env_dict["ARTIFACT_EXCLUDES"], ["e", "n", "v"])

    self.assertEquals(env_dict["NEW_ENV_SETTING"], "new env setting")
    self.assertFalse("NOT_IN_TOTO_NOTHING" in env_dict)


  def test_set_settings(self):
    in_toto.user_settings.set_settings()
    # RCfile settings have precedence over env settings
    self.assertEquals(in_toto.settings.ARTIFACT_BASEPATH, "r/c/file")
    self.assertListEqual(in_toto.settings.ARTIFACT_EXCLUDES, ["r", "c", "file"])
    self.assertEquals(in_toto.settings.NEW_RC_SETTING, "new rc setting")

    # Settings that are only in env are still used even if they are new
    self.assertEquals(in_toto.settings.NEW_ENV_SETTING, "new env setting")

if __name__ == "__main__":
  unittest.main()
