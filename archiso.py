#!/usr/bin/env python

from metadata_encoder import Layout, Link, Validation, Subchain

if __name__:

    profile = Link(name="profiling", materials=[], 
                        products=["pin profile_file"], 
                        pubkeys=["PUBKEY"])

    edit_folder_structure = Link(name="edit_folder_structure",  
                     materials=[], 
                     products=["update folders.tar.gz"], 
                     pubkeys=["PUBKEY"])

    bootloader_config = Link(name="bootloader_config",  
                     materials=["match product folders.tar.gz from"
                                "edit_folder_structure"], 
                     products=["update folders.tar.gz"], 
                     pubkeys=["PUBKEY"])


    login_config = Link(name="login_config",  
                     materials=["match product folders.tar.gz from"
                                "bootloader_config"], 
                     products=["update folders.tar.gz"], 
                     pubkeys=["PUBKEY"])

    upstream = Subchain(name="upstream", materials=[], 
                        products=["update clone.sh"], 
                        pubkeys=["PUBKEY"])

    versioning = Link("versioning", 
                   materials=["match clone.sh from upstream"], 
                        products=["pin build.sh"],
                        pubkeys=["PUBKEY"])

    build = Link(name="build", 
                     materials=["match build.sh from versioning",
                                "match folders.tar.gz from login_config"], 
                        products=["archlinux-multiarch.iso"], 
                        pubkeys=["PUBKEY"])

    verify_rsl = Validation(name="verify_rsl", run="toto-link",
                            flags=["validate_rsl", "-p", "PUBKEYS"],
                            materials=[],
                            products=["match bulid.sh * from upstream",])

    layout = Layout([profile, edit_folder_structure, bootloader_config,
                     login_config, upstream, versioning, build, verify_rsl], 
            [{'key1':{'pubkey':"stuff"}}, 
             {'key2': {'pubkey': "stuff"}}])

    print("{}".format(layout))
