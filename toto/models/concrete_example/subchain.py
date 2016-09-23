#!/usr/bin/env python

from layout import Layout, Link

if __name__:

    make_modules = Link(name="build_modules", 
                    materials=[["MATCH", "PRODUCT", "*", "FROM", "huh?"]], 
                    expected_command={'run':"make",
                                "flags":["modules"]},
                        products=[["CREATE", "build/modules/*"]], 
                        pubkeys=["subkey1"])

    make_kernel = Link(name="build_kernel", 
                    materials=[["MATCH", "PRODUCT", "*", "FROM", "huh?"]], 
                    expected_command={'run':"make",
                                "flags":[]},
                        products=[["CREATE", "arch/x86/boot/bzImage"]], 
                        pubkeys=["subkey2"])


    l = Layout([make_modules, make_kernel],
            [{'subkey1':{'pubkey':"stuff"}}, 
             {'subkey2': {'pubkey': "stuff"}}],
            expires='never')

    print("{}".format(l))
