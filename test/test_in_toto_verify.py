#!/usr/bin/env python

"""
    TODO: this
"""

import unittest

class Test(unittest.TestCase):

  @unittest.skip("Missing test implementation")
  def test_unimplemented(self):
    raise self.assertFalse("Missing test implementation!")

# Run unit test.
if __name__ == '__main__':
  unittest.main()
