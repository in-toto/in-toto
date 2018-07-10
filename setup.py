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

  # Recommended Tools
    - git (git-scm.com)
    - pip (pip.pypa.io)
    - virtualenvs - optional but strongly recommended!
      (http://docs.python-guide.org/en/latest/dev/virtualenvs/)

  # Installation from GitHub
    ```
    pip install git+https://github.com/in-toto/in-toto@develop
    ```
"""
from setuptools import setup, find_packages

version = "0.2.dev3"

setup(
  name="in-toto",
  version=version,
  author="New York University: Secure Systems Lab",
  author_email="in-toto-dev@googlegroups.com",
  url="https://in-toto.io",
  description=("A framework to define and secure the integrity of "
    "software supply chains"),
  long_description=("To learn more about in-toto visit our source code "
    "`repository on GitHub "
    "<https://github.com/in-toto/in-toto/tree/{version}>`__."
    .format(version=version)),
  license="MIT",
  keywords="software supply chain security",
  classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Natural Language :: English',
    'Operating System :: POSIX',
    'Operating System :: POSIX :: Linux',
    'Operating System :: MacOS :: MacOS X',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: Implementation :: CPython',
    'Topic :: Security',
    'Topic :: Software Development'
  ],
  packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests",
      "debian"]),
  install_requires=["six", "securesystemslib[crypto,pynacl]>=0.11.2", "attrs",
                    "python-dateutil", "iso8601"],
  test_suite="tests.runtests",
  entry_points={
    "console_scripts": ["in-toto-run = in_toto.in_toto_run:main",
                        "in-toto-mock = in_toto.in_toto_mock:main",
                        "in-toto-record = in_toto.in_toto_record:main",
                        "in-toto-verify = in_toto.in_toto_verify:main",
                        "in-toto-sign = in_toto.in_toto_sign:main",
                        "in-toto-keygen = in_toto.in_toto_keygen:main"]
  },
)
