#!/usr/bin/env python

from metadata_encoder import Layout, Link, Validation, Subchain

if __name__:

    pre_release= Subchain(name="pre-release", materials=[], 
                        products=[["CREATE", "*"]], 
                        pubkeys=["key1"])

    build_test = Subchain(name="build-test",  
                     materials=[["MATCH", "PRODUCT", "*", "FROM", "pre-release"]], 
                     products=[["CREATE", "files.tar.gz"],
                               ["DROP", "*"]], 
                     pubkeys=["key2"])

    package = Link("pypi-package", 
                   expected_command={'run': 'python',
                                     'flags': ['setup.py', 'sdist']},
                   materials=[["MATCH", "PRODUCT", "files.tar.gz", "FROM",
                       "build-test"]], 
                   products=[["CREATE", "django.python27.egg"]],
                   pubkeys=["key3"])

    verify_rsl = Validation(name="verify_rsl", 
                            command={'run':"toto-link",
                                'flags':["validate_rsl", "-p", "PUBKEYS"]},
                            materials=[],
                            products=[["MATCH", "MATERIAL", "*", "FROM",
                                "pre-release",]])

    layout = Layout([pre_release, build_test, package, verify_rsl],
            [{'key1':{'pubkey':"stuff"}}, 
             {'key2': {'pubkey': "stuff"}},
             {'key3': {'pubkey': "stuff"}}])

    print("{}".format(layout))
