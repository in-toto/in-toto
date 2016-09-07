#!/usr/bin/env python

from metadata_encoder import Layout, Link, Validation, Subchain

if __name__:

    profile = Link(name="profiling", materials=[], 
                        expected_command={'run': "",
                                'flags': []},
                        products=[["CREATE", "profile_file"]], 
                        pubkeys=["key1"])

    edit_folder_structure = Link(name="edit_folder_structure",  
                    expected_command={'run': "",
                                       'flags': []},
                     materials=[], 
                     products=[["MODIFY", "folders.tar.gz"]], 
                     pubkeys=["key1"])

    bootloader_config = Link(name="bootloader_config",  
                     materials=[["MATCH", "PRODUCT", "folders.tar.gz", "FROM",
                                " edit_folder_structure"]], 
                    expected_command={'run': "",
                                       'flags': []},
                     products=[["MODIFY", "folders.tar.gz"]], 
                     pubkeys=["key2"])


    login_config = Link(name="login_config",  
                     materials=[["MATCH", "PRODUCT",  "folders.tar.gz", "FROM",
                                " bootloader_config"]], 
                    expected_command={'run': "",
                                       'flags': []},
                     products=[["MODIFY",  "folders.tar.gz"]], 
                     pubkeys=["key2"])

    upstream = Subchain(name="upstream", materials=[], 
                        products=[["MODIFY", "clone.sh"]], 
                        pubkeys=["key2"])

    versioning = Link("versioning", 
                    expected_command={'run': "",
                                       'flags': []},
                   materials=[["MATCH", "PRODUCT", "clone.sh", "FROM", 
                              "upstream"]], 
                        products=[["CREATE", "build.sh"]],
                        pubkeys=["key1"])

    build = Link(name="build", 
                    expected_command={'run': "",
                                       'flags': []},
            materials=[["MATCH", "PRODUCT", "build.sh", "FROM", "versioning"],
                       ["MATCH", "PRODUCT", "folders.tar.gz", "FROM", "login_config"]], 
                        products=[["CREATE", "archlinux-multiarch.iso"]], 
                        pubkeys=["key1"])

    verify_rsl = Validation(name="verify_rsl", 
                            command={"run":"validate_rsl",
                                "flags":["-p", "GPG_KEYRING"],},
                            materials=[],
                            products=[["MATCH", "PRODUCT", "bulid.sh",
                                "FROM","upstream",]])

    layout = Layout([profile, edit_folder_structure, bootloader_config,
                     login_config, upstream, versioning, build, verify_rsl], 
            [{'key1':{'pubkey':"stuff"}}, 
             {'key2': {'pubkey': "stuff"}}])

    print("{}".format(layout))
