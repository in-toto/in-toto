#!/usr/bin/env python

from layout import Layout, Step, Validation
from matchrules import Create, Match

if __name__:

    upstream = Step(name="upstream", materials=[], 
                    expected_command={'run':"git",
                                "flags":["tag"]},
                        products=[Create("*").encode()], 
                        pubkeys=["key1"])

    buildbot = Step(name="buildbot",  
                    expected_command={'run':"buildbot",
                                "flags":["run"]},
                     materials=[Match("PRODUCT", "*", upstream._name).encode()], 
                     products=[], 
                     pubkeys=["key2"])

    l = Layout([upstream, buildbot],
            [{'key1':{'pubkey':"stuff"}}, 
             {'key2': {'pubkey': "stuff"}}],
             "now")

    print("{}".format(l))
