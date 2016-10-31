#!/usr/bin/env python
"""
  TODO: this
"""
from setuptools import setup, find_packages

setup(
  name="toto-framework",
  version="0.0.1",
  author="New York University: Secure Systems Lab",
  author_email="santiago@nyu.edu",
  description=("A framework to define and secure "
               "the integrity of software supply chains"),
  license="MIT",
  packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
  install_requires=['six', 'simple-settings', 'attrs', 'canonicaljson',
                    'python-dateutil', 'iso8601'],
  test_suite="test.runtests",
  scripts=['toto/toto-run.py',
           'toto/toto-verify.py']
)
