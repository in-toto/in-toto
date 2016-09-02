#!/usr/bin/env python

from metadata_encoder import Layout, Link, Validation, Subchain

if __name__:

    upstream = Link(name="upstream", materials=[], 
                        products=["pin *"], 
                        pubkeys=["PUBKEY"])

    buildbot = Link(name="buildbot",  
                     materials=["match product * from upstream"], 
                     products=[], 
                     pubkeys=["PUBKEY"])

    layout = Layout([upstream, buildbot],
            [{'key1':{'pubkey':"stuff"}}, 
             {'key2': {'pubkey': "stuff"}}])

    print("{}".format(layout))
