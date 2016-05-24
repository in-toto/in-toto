#!/usr/bin/env python
"""
    TODO: this
"""
from setuptools import setup

setup(
    name="Toto",
    version="0.0.1",
    author="Santiago Torres",
    author_email="santiago@nyu.edu",
    description=("Toto is a series of scripts to verify the integrity"
                 "of the software supply chain"),
    license="MIT",
    packages=["toto"],
    install_requires=[
        ],
    test_suite="test.runtests",
)
