"""
<Program Name>
  toto-run.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  June 27, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides a command line interface which takes any link command of the software 
  supply chain as input and wraps toto metadata recording. 

  Toto run options are separated from the command to be executed by 
  a double dash.

  Example Usage
  ```
  python -m toto.toto-run --material <files> --product <files> -- 
    <command-to-execute> <command-options-and-arguments> | edit
  ```

  The actual wrapper and the tasks it performs are implemented in runlib.

  TODO
    * Material/Product
      For now we specify --materials and --products explicitly. Later we can think
      of more sophisticate/secure ways to find out which files are being 
      transformed
"""

import os
import sys
import argparse
import toto.util
import toto.runlib


def main():
  # Create new parser with custom usage message
  parser = argparse.ArgumentParser(
      description="Executes link command and records metadata",
      usage="python -m %s --name <unique name>\n" \
            "            [--materials <filepath>[,<filepath> ...]]\n" \
            "             --products <filepath>[,<filepath> ...]\n" \
            "             --key <filepath>\n" \
            "             -- <cmd> [args]" % (os.path.basename(__file__), ))

  # Option group for toto specific options, e.g. material and product
  toto_args = parser.add_argument_group("Toto options")

  # XXX LP: Name has to be unique!!! Where will we check this?
  # XXX LP: Do we limit the allowed characters for the name?
  # XXX LP: Should it be possible to add a path?
  toto_args.add_argument("-n", "--name", type=str, required=True,
      help="Unique name for link metadata")

  # XXX LP: We should allow path wildcards here and sanitze them
  toto_args.add_argument("-m", "--materials", type=str, required=True,
      help="Files to recorded before link command execution")
  toto_args.add_argument("-p", "--products", type=str, required=True,
      help="Files to record after link command execution")

  # XXX LP: Specifiy a format or choice of formats to use,
  # For now it is "ssl_crypto.formats.RSAKEY_SCHEMA"
  toto_args.add_argument("-k", "--key", type=str, required=True,
      help="Path to private key (<FORMAT>) to sign link metadata")

  # Option group for link command to be executed
  link_args = parser.add_argument_group("Link command")

  # XXX: This is not yet ideal. 
  # What should we do with tokens like > or ;
  link_args.add_argument('link_cmd', nargs="+", 
    help="link command to be executed with options and arguments")

  args = parser.parse_args()

  # XXX LP: Sanitze more?
  name = args.name
  materials = args.materials
  products = args.products
  link_cmd = args.link_cmd

  ## XXX LP: This will be changed
  key = toto.util.create_and_persist_or_load_key(args.key)

  if materials:
    materials = materials.split(",")
  if products:
    products = products.split(",")

  # try:
  toto.runlib.run_link(name, materials, products, link_cmd, key)
  # except Exception, e:
  #   raise e

if __name__ == '__main__':
  main()
