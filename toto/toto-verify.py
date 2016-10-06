#!/usr/bin/env python
"""
<Program Name>
  toto-verify.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Oct 3, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides a command line interface that wraps the verification of
  toto final product.

  The actual verification is implemented in verifylib.

  Example Usage:
  ```
  python -m toto.toto-verify --layout <root.layout> --layout-key <layout-key>
  ```

  Todo:
    - Maybe move some of the parts of verifylib over here

"""
import sys
import argparse

import toto.util
import toto.verifylib

def main():  # Create new parser with custom usage message

  parser = argparse.ArgumentParser(
      description="Verifies a toto bunle",
      usage="python -m %s --layout <root layout name>\n" \
            "             --layout-key <root layout public key>")

  toto_args = parser.add_argument_group("Toto options")

  toto_args.add_argument("-l", "--layout", type=str, required=True,
      help="Root layout to use for verification")

  # XXX LP: This could be more than one
  toto_args.add_argument("-k", "--layout-key", type=str, required=True,
    help="Key to verify root layout signature")

  args = parser.parse_args()

  retval = toto.verifylib.toto_verify(args.layout, args.layout_key)
  sys.exit(retval)

if __name__ == '__main__':
  main()
