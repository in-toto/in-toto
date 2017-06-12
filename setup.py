#!/usr/bin/env python
"""
  TODO: this
"""
from setuptools import setup, find_packages

setup(
  name="in-toto",
  version="0.0.1",
  author="New York University: Secure Systems Lab",
  author_email=["santiago@nyu.edu", "lukas.puehringer@nyu.edu"],
  description=("A framework to define and secure "
               "the integrity of software supply chains"),
  license="MIT",
  packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
  install_requires=["six", "securesystemslib==0.10.4", "attrs", "canonicaljson",
                    "python-dateutil", "iso8601"],
  test_suite="test.runtests",
  entry_points={
    "console_scripts": ["in-toto-run = in_toto.in_toto_run:main",
                        "in-toto-mock = in_toto.in_toto_mock:main",
                        "in-toto-record = in_toto.in_toto_record:main",
                        "in-toto-verify = in_toto.in_toto_verify:main"]
  },
)
