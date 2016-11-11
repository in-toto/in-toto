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
  toto-verify.py --layout <root.layout> --layout-keys <layout-key>
  ```

"""
import sys
import argparse
import toto.util
import toto.verifylib
import toto.log as log

def main():
  parser = argparse.ArgumentParser(
      description="Verifies in-toto final product",
      usage=("toto-verify.py --layout <layout path>\n" +
             "                      --layout-keys (<layout pubkey path>,...)"))

  toto_args = parser.add_argument_group("Toto options")

  toto_args.add_argument("-l", "--layout", type=str, required=True,
      help="Root layout to use for verification")

  toto_args.add_argument("-k", "--layout-keys", type=str, required=True,
    help="Key(s) to verify root layout signature (separated ',')")

  args = parser.parse_args()

  layout_key_paths = args.layout_keys.split(',')
  toto.verifylib.in_toto_verify(args.layout, layout_key_paths)

if __name__ == '__main__':
  main()
