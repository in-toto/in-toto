#!/usr/bin/env python

from metadata_encoder import Layout, Link, Validation

if __name__:

    git = Link(name="git", 
               expected_command={'run':'git',
                                 'flags':['tag']},
               materials=[], 
               products=[["CREATE", "*"]], pubkeys=["key1"])

    comp = Link(name="compile",  
                expected_command={'run': 'gcc',
                                  'flags':['-O3', '-Wall', '--gnu-source']},
                materials=[["MATCH", "PRODUCT", "*", "FROM", "git"]], 
                products=[["CREATE", "foo.exe"]], pubkeys=["key2"])

    tar = Link(name="pack", 
                expected_command={'run': 'tar',
                                  'flags': ['-zcvf', 'foo.exe']},
                materials=[["MATCH", "PRODUCT", "*", "FROM", "comp"],
                           ["MATCH", "PRODUCT", "LICENSE", "FROM", "git"],
                           ["DROP", "*"]], 
                        products=[["CREATE", "pkg.tar.gz"]],
                        pubkeys=["key2"])

    untar = Validation(name="untar", 
                 command={'run':"toto-link", 
                     'flags':["tar", "-zxvf", "pkg.tar.gz"]},
                 materials=[["MATCH", "PRODUCT", "pkg.tar.gz", "FROM", "pack"]],
                 products=[["MATCH", "PRODUCT", "*", "FROM", "comp"]])

    verify_rsl = Validation(name="verify_rsl", 
                            command={'run':"validate_rsl",
                                "flags":["rsl", "-p", "PUBKEYS"]},
                            materials=[["MATCH", "PRODUCT", "*", "FROM",
                                        "git"]],
                            products=[])

    layout = Layout([git, comp, tar, untar, verify_rsl],
            [{'key1':{'pubkey':"stuff"}}, 
             {'key2': {'pubkey': "stuff"}}])

    print("{}".format(layout))
