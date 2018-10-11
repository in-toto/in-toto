"""
<Program Name>
  test_log.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Jan 30, 2018

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test in_toto/log.py

"""
import logging
import unittest
import in_toto.log


class TestInTotoLogger(unittest.TestCase):
  def test_set_level_verbose_or_quiet(self):
    """Test set level convenience method. """
    logger = in_toto.log.InTotoLogger("test-in-toto-logger")

    # Default level if verbose and quiet are false
    logger.setLevelVerboseOrQuiet(False, False)
    self.assertEqual(logger.level, logging.NOTSET)

    # INFO if verbose is true
    logger.setLevelVerboseOrQuiet(True, False)
    self.assertEqual(logger.level, logging.INFO)

    # CRITICAL if quiet is true
    logger.setLevelVerboseOrQuiet(False, True)
    self.assertEqual(logger.level, logger.QUIET)


if __name__ == "__main__":
  unittest.main()
