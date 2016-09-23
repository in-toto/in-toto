#!/usr/bin/env python

from layout import Layout, Link, Validation, Delegation 

if __name__:

    upstream = Link(name="upstream", materials=[], 
                    expected_command={'run':"git",
                                "flags":["tag"]},
                        products=[["CREATE", "src/*"]], 
                        pubkeys=["key1"])

    buildbot = Delegation(name="buildbot",  
                     materials=[["MATCH", "PRODUCT", "src/*", "FROM", "upstream"]], 
                     products=[["CREATE", "build/modules/*"], 
                               ["CREATE", "arch/x86/bzImage"]],
                     pubkeys=["key2"])

    package = Link(name="package", 
            expected_command={'run':"make",
                              'flags':["dist"]},
                   materials=[["MATCH", "PRODUCT", "*", "FROM", "buildbot"]],
                   products=[["CREATE", "linux.tar.gz"]],
                   pubkeys=['key3'])
                    

    l = Layout([upstream, buildbot, package],
            [{'key1':{'pubkey':"stuff"}}, 
             {'key2': {'pubkey': "stuff"}},
             {'key3': {'pubkey': "stuff"}}
            ],
            expires="never")

    print("{}".format(l))
