#!/usr/bin/env python

from layout import Layout, Link, Validation, Subchain

if __name__:

    upstream = Subchain(name="upstream", materials=[["CREATE", "*"]], 
                        products=[["CREATE", "orig.tar.gz"]], 
                        pubkeys=["key2"])

    debianize = Link(name="debianize",  
                    expected_command={'run': "",
                              'flags': []},
                     materials=[["MATCH", "PRODUCT", "orig.tar.gz", "FROM",
                         "upstream"]], 
                     products=[["CREATE", "diff.tar.gz"]], 
                     pubkeys=["key1"])

    package = Link("package", 
                    expected_command={'run': "debbuild",
                              'flags': ['-c', 'diff.tar.gz']},
                   materials=[["MATCH", "PRODUCT", "orig.tar.gz", "FROM",
                       "upstream"],
                              ["MATCH", "PRODUCT", "diff.tar.gz", "FROM",
                              "debianize"]],
                        products=[["CREATE", "package.deb"]],
                        pubkeys=["key1"])

    dpkg = Validation(name="dpkgg", 
                command={'run':"dpkg", 
                         "flags":["-i", "package.deb"]},
                 materials=[["MATCH", "PRODUCT", "package.deb",
                     "FROM","package"]],
                 products=[["MATCH", "MATERIAL", "*", "FROM", "upstream"]])

    verify_rsl = Validation(name="verify_rsl", 
                            command={'run':"toto-link",
                                "flags":["validate_rsl", "-p", "PUBKEYS"]},
                            materials=[],
                            products=[["MATCH", "MATERIAL", "*", "FROM",
                                "upstream"]])

    l = Layout([upstream, debianize, package, dpkg, verify_rsl],
            [{'key1':{'pubkey':"stuff"}}, 
             {'key2': {'pubkey': "stuff"}}])

    print("{}".format(l))
