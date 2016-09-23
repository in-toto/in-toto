#!/usr/bin/env python

from link import Link

if __name__:

    upstream = Link(name="upstream", materials=[], 
                    command_ran="git tag 1.0",
                    products=[["src/foo", "HASH"],
                                  ["src/bar", "HASH"],
                                  ["src/baz", "HASH"],
                                  ],
                    return_value=0)

    make_modules = Link(name="build_modules", 
                    materials=[["src/foo", "HASH",],
                                ["src/bar", "HASH"],
                                ["src/baz", "HASH"],
                                  ],
                    command_ran="make modules",
                    products=[["build/modules/foo.ko", "HASH"],
                              ["build/modules/bar.ko", "HASH"],
                               ], 
                    return_value=0)

    make_kernel = Link(name="build_kernel", 
                    materials=[["src/foo", "HASH",],
                                ["src/bar", "HASH"],
                                ["src/baz", "HASH"],
                                  ],
                    command_ran="make",
                    products=[["arch/x86/boot/bzImage", "HASH"]], 
                    return_value=0)

    package = Link(name="package", 
                   command_ran="make dist",
                   materials=[["arch/x86/boot/bzImage", "HASH"],
                              ["build/modules/foo.ko", "HASH"],
                              ["build/modules/bar.ko", "HASH"],
                              ],
                   products=[["linux.tar.gz", "HASH"]],
                   return_value=0)

    for metadata in [upstream, make_modules, make_kernel, package]:
        filename = "{}.link".format(metadata._name)
        with open(filename, "wt") as fp:
            fp.write("{}".format(metadata))
