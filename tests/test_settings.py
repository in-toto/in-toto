"""
<Program Name>
  test_settings.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Jan 30, 2018

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test in_toto/settings.py

"""
import unittest
import in_toto.settings


class TestSettings(unittest.TestCase):
  def test_debug_not_true(self):
    """in_toto.settings.DEBUG should not be commited with True. """
    self.assertFalse(in_toto.settings.DEBUG)

if __name__ == "__main__":
  unittest.main()
