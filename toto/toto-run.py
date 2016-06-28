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
  Provide a command line interface which takes any link command of the software 
  supply chain as input and wraps toto metadata recording around it. 

  Toto run options are separated from the command to be executed by 
  a double dash.

  Example Usage
  ```
  python -m toto.toto-run --material <files> --product <files> -- 
    <command-to-execute> <command-options-and-arguments>
  ```

  The actual wrapper and the tasks it performs are implemented in runlib.

  TODO
    * Material/Product
      For now we specify --material and --product explicitly. Later we can think
      of more sophisticate/secure ways to find out which files are being
    * Missing options:
      - Unique identifier to assign to link definition in layout
      - Key (for now uses a default key)

"""

import os
import sys
import argparse

import toto.runlib



def main():
  # Create new parser with custom usage message
  parser = argparse.ArgumentParser(
      description="Executes link command and records metadata",
      usage="python -m %s -m DIR -p DIR -- CMD [args]" % 
      (os.path.basename(__file__), ))

  # Option group for toto specific options, e.g. material and product
  toto_args = parser.add_argument_group("Toto options")
  toto_args.add_argument("-m", "--material", type=str, required=True,
      help="directory before link command execution")
  toto_args.add_argument("-p", "--product", type=str, required=True,
      help="directory after link command execution")

  # Option group for link command to be executed
  link_args = parser.add_argument_group("Link command")

  # XXX: This is not yet ideal. 
  # What should we do with tokens like > or ;
  link_args.add_argument('link_cmd', nargs="+", 
    help="link command to be executed with options and arguments")

  args = parser.parse_args()

  # try:
  toto.runlib.run_link(args.material, args.link_cmd, args.product)
  # except Exception, e:
  #   raise e


if __name__ == '__main__':
  main()