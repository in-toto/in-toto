#!/usr/bin/env python
"""
    TODO: this documentation!
"""

from unittest import defaultTestLoader, TextTestRunner
import sys

suite = defaultTestLoader.discover(start_dir=".")
result = TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
