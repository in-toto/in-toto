#!/usr/bin/env python

from metadata_encoder import Layout, Link, Validation, Subchain

if __name__:

    pre_release= Subchain(name="pre-release", materials=[], 
                        products=["pin *"], 
                        pubkeys=["PUBKEY"])

    configure_lb= Link(name="configure_lb",  
                     materials=["match product * from pre-release"], 
                     products=["pin lb_config"], 
                     pubkeys=["PUBKEY"])

    clone_lb = Subchain("clone_lb", 
                   materials=[], 
                   products=["pin *"],
                   pubkeys=["PUBKEY"])

    build = Link(name="build",  
                     materials=["match product * from clone_lb",
                                "match product lb_conig from configure_lb",
                                "match product * from pre_release"], 
                     products=["pin *"], 
                     pubkeys=["PUBKEY"])

    verify_rsl = Validation(name="verify_rsl", run="toto-link",
                            flags=["validate_rsl", "-p", "PUBKEYS"],
                            materials=[],
                            products=["pin tails.iso"])

    layout = Layout([pre_release, configure_lb, clone_lb, build, verify_rsl],
            [{'key1':{'pubkey':"stuff"}}, 
             {'key2': {'pubkey': "stuff"}}])

    print("{}".format(layout))
