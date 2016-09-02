#!/usr/bin/env python

from metadata_encoder import Layout, Link, Validation, Subchain

if __name__:

    upstream = Subchain(name="upstream", materials=["pin *"], 
                        products=["pin orig.tar.gz"], 
                        pubkeys=["PUBKEY"])

    debianize = Link(name="debianize",  
                     materials=["match product orig.tar.gz from upstream"], 
                     products=["pin diff.tar.gz"], 
                     pubkeys=["PUBKEY"])

    package = Link("package", 
                   materials=["match product orig.tar.gz from upstream",
                              "match product diff.tar.gz from debianize"], 
                        products=["pin package.deb"],
                        pubkeys=["PUBKEY"])

    dpkg = Validation(name="dpkgg", run="dpkg", 
                 flags=["-i", "package.deb"],
                 materials=["match product package.deb from package"],
                 products=["match material * from upstream"])

    verify_rsl = Validation(name="verify_rsl", run="toto-link",
                            flags=["validate_rsl", "-p", "PUBKEYS"],
                            materials=[],
                            products=["match material * from upstream",])

    layout = Layout([upstream, debianize, package, dpkg, verify_rsl],
            [{'key1':{'pubkey':"stuff"}}, 
             {'key2': {'pubkey': "stuff"}}])

    print("{}".format(layout))
