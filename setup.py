#!/usr/bin/env python
"""
<Program Name>
  setup.py

<Author>
  Santiago Torres <santiago@nyu.edu>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  May 23, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  setup.py script to install in-toto framework and in-toto scripts

  # System Dependencies
    - Python2.7 (www.python.org)
    - OpenSSL (www.openssl.org)
    - git (git-scm.com)
    - pip (pip.pypa.io)
    - virtualenvs - optional but strongly recommended!
      (http://docs.python-guide.org/en/latest/dev/virtualenvs/)

  # Installation from GitHub
    ```
    pip install git+git://github.com/in-toto/in-toto@develop
    ```
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
                        "in-toto-verify = in_toto.in_toto_verify:main",
                        "in-toto-sign = in_toto.in_toto_sign:main",
                        "in-toto-keygen = in_toto.in_toto_keygen:main"]
  },
)
