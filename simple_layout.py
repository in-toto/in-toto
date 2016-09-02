#!/usr/bin/env python

from metadata_encoder import Layout, Link, Validation

if __name__:

    git = Link(name="git", materials=[], products=["pin *"], pubkeys=["PUBKEY"])

    comp = Link(name="compile",  materials=["match * from git"], 
                products=["pin foo.exe"], pubkeys=["PUBKEY"])

    tar = Link("pack", materials=["match product * from comp",
                                         "match product LICENSE from git",
                                         "drop *"], 
                        products=["pin pkg.tar.gz"],
                        pubkeys=["PUBKEY"])

    untar = Validation(name="untar", run="toto-link", 
                 flags=["tar", "-zxvf", "pkg.tar.gz"],
                 materials=["match product pkg.tar.gz from pack"],
                 products=["match product * from comp"])

    verify_rsl = Validation(name="verify_rsl", run="toto-link",
                            flags=["validate_rsl", "-p", "PUBKEYS"],
                            materials=["match * from git",],
                            products=[])

    layout = Layout([git, comp, tar, untar, verify_rsl],
            [{'key1':{'pubkey':"stuff"}}, 
             {'key2': {'pubkey': "stuff"}}])

    print("{}".format(layout))
