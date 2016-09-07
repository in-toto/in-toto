#!/usr/bin/env python

from metadata_encoder import Layout, Link, Validation, Subchain

if __name__:

    upstream = Link(name="upstream", materials=[], 
                    expected_command={'run':"git",
                                "flags":["tag"]},
                        products=[["CREATE", "*"]], 
                        pubkeys=["key1"])

    buildbot = Link(name="buildbot",  
                    expected_command={'run':"buildbot",
                                "flags":["run"]},
                     materials=[["MATCH", "PRODUCT", "*", "FROM", "upstream"]], 
                     products=[], 
                     pubkeys=["key2"])

    layout = Layout([upstream, buildbot],
            [{'key1':{'pubkey':"stuff"}}, 
             {'key2': {'pubkey': "stuff"}}])

    print("{}".format(layout))
