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

  See https://in-toto.readthedocs.io/en/latest/installing.html for installation
  instructions.

"""
import io
import os
import re

from setuptools import setup, find_packages


base_dir = os.path.dirname(os.path.abspath(__file__))

def get_version(filename="in_toto/__init__.py"):
  """
  Gather version number from specified file.

  This is done through regex processing, so the file is not imported or
  otherwise executed.

  No format verification of the resulting version number is done.
  """
  with io.open(os.path.join(base_dir, filename), encoding="utf-8") as initfile:
    for line in initfile.readlines():
      m = re.match("__version__ *= *['\"](.*)['\"]", line)
      if m:
        return m.group(1)

with open("README.md") as f:
  long_description = f.read()

setup(
  name="in-toto",
  author="New York University: Secure Systems Lab",
  author_email="in-toto-dev@googlegroups.com",
  url="https://in-toto.io",
  description=("A framework to define and secure the integrity of "
    "software supply chains"),
  long_description_content_type="text/markdown",
  long_description=long_description,
  license="Apache-2.0",
  keywords="software supply chain security",
  classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Apache Software License',
    'Natural Language :: English',
    'Operating System :: POSIX',
    'Operating System :: POSIX :: Linux',
    'Operating System :: MacOS :: MacOS X',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: Implementation :: CPython',
    'Topic :: Security',
    'Topic :: Software Development'
  ],
  python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, <4",
  packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests",
      "debian"]),
  install_requires=["six", "securesystemslib[crypto]>=0.18.0", "attrs",
                    "python-dateutil", "iso8601", "pathspec"],
  extras_require={
    # Install pynacl as optional dependency to use with securesystemslib, as a
    # workaround for `"ssl-pynacl": ["securesystemslib[pynacl]>=0.11.3"]`,
    # which currently is not supported in "extra_require" (see pypa/pip#4957).
    # TODO: Keep track of changes (version, additional requirements) under the
    # "pynacl" key in securesystemslib's setup.py.
    # https://github.com/secure-systems-lab/securesystemslib/blob/master/setup.py#L101
    "pynacl": ["pynacl>1.2.0"]
  },
  test_suite="tests.runtests",
  tests_require=["mock"],
  entry_points={
    "console_scripts": ["in-toto-run = in_toto.in_toto_run:main",
                        "in-toto-mock = in_toto.in_toto_mock:main",
                        "in-toto-record = in_toto.in_toto_record:main",
                        "in-toto-verify = in_toto.in_toto_verify:main",
                        "in-toto-sign = in_toto.in_toto_sign:main",
                        "in-toto-keygen = in_toto.in_toto_keygen:main"]
  },
  project_urls={
    "Source": "https://github.com/in-toto/in-toto",
    "Bug Reports": "https://github.com/in-toto/in-toto/issues",
  },
  version=get_version(),
)
