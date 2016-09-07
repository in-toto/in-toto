#!/usr/bin/env python

from metadata_encoder import Layout, Link, Validation, Subchain

if __name__:

    pre_release= Subchain(name="pre-release", materials=[], 
                        products=[["CREATE", "*"]],
                        pubkeys=["key1"])

    configure_lb= Link(name="configure_lb",  
                     materials=[["MATCH", "PRODUCT", "*", "FROM", "pre-release"]], 
                     expected_command={"run": "toto_vi",
                                        "flags": []},
                     products=[["CREATE", "lb_config"]], 
                     pubkeys=["key2"])

    clone_lb = Subchain("clone_lb", 
                   materials=[], 
                   products=[["MODIFY", "*"]],
                   pubkeys=["key2"])

    build = Link(name="build",  
                     materials=[["MATCH", "PRODUCT", "*", "FROM", "clone_lb"],
                                ["MATCH", "PRODUCT", "lb_conig", "FROM",
                                "configure_lb"],
                                ["MATCH", "PRODUCT", "*", "FROM", "pre_release"]], 
                     expected_command = {"run": "lb_build",
                                         "flags": []},
                     products=[["MODIFY", "*"]], 
                     pubkeys=["key2"])

    verify_rsl = Validation(name="verify_rsl", command={'run':"toto-link",
                            'flags':["validate_rsl", "-p", "PUBKEYS"]},
                            materials=[],
                            products=[["CREATE", "tails.iso"]])

    layout = Layout([pre_release, configure_lb, clone_lb, build, verify_rsl],
            [{'KEYID1':{'pubkey':"stuff"}}, 
             {'KEYID2': {'pubkey': "stuff"}}])

    print("{}".format(layout))
