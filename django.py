#!/usr/bin/env python

from metadata_encoder import Layout, Link, Validation, Subchain

if __name__:

    pre_release= Subchain(name="pre-release", materials=[], 
                        products=["pin *"], 
                        pubkeys=["PUBKEY"])

    build_test = Subchain(name="build-test",  
                     materials=["match product * from pre-release"], 
                     products=["pin files.tar.gz",
                               "drop *"], 
                     pubkeys=["PUBKEY"])

    package = Link("pypi-package", 
                   materials=["match product files.tar.gz from build-test"], 
                   products=["pin django.python27.egg"],
                   pubkeys=["PUBKEY"])

    verify_rsl = Validation(name="verify_rsl", run="toto-link",
                            flags=["validate_rsl", "-p", "PUBKEYS"],
                            materials=[],
                            products=["match material * from pre-release",])

    layout = Layout([pre_release, build_test, package, verify_rsl],
            [{'key1':{'pubkey':"stuff"}}, 
             {'key2': {'pubkey': "stuff"}}])

    print("{}".format(layout))
