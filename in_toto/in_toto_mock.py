#!/usr/bin/env python
"""
<Program Name>
  in_toto_mock.py

<Author>
  Shikher Verma <root@shikherverma.com>

<Started>
  June 12, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Stripped down variant of in-toto-run command that can be used to mock metadata
  generation of in-toto-run, without the need to specify a key and knowing all
  the command line arguments. Generated MockLink is unsigned and includes working
  directory, byproducts and used current directory as material and products.

  Provides a command line interface which takes any link command of the software
  supply chain as input and generates mock in_toto metadata.

  in_toto_mock options are separated from the command to be executed by
  a double dash.

  The implementation of the tasks can be found in runlib.

  Example Usage
  ```
  in-toto-mock --name write-code -- touch foo.py
  ```

"""

import sys
import argparse
import logging
import in_toto.runlib

# Command line interfaces should use in_toto base logger (c.f. in_toto.log)
log = logging.getLogger("in_toto")


def in_toto_mock(name, link_cmd_args):
  """
  <Purpose>
    Calls runlib.in_toto_mock with name and link_cmd_args.

  <Arguments>
    name:
            A unique name to relate mock link metadata with a step defined
            in the layout.
    link_cmd_args:
            A list where the first element is a command and the remaining
            elements are arguments passed to that command.

  <Exceptions>
    SystemExit if any exception occurs

  <Side Effects>
    Calls sys.exit(1) if an exception is raised

  <Returns>
    None.
  """

  try:
    in_toto.runlib.in_toto_mock(name, link_cmd_args)
  except Exception as e:
    log.error("in toto mock - {}".format(e))
    sys.exit(1)

def main():
  """Parse arguments and call in_toto_mock. """
  parser = argparse.ArgumentParser(
      description="Executes link command and records metadata")
  # Whitespace padding to align with program name
  lpad = (len(parser.prog) + 1) * " "

  parser.usage = ("\n"
      "%(prog)s  --name <unique step name>\n{0}"
               " -- <cmd> [args]\n\n"
               .format(lpad))

  in_toto_args = parser.add_argument_group("in-toto options")

  # FIXME: Do we limit the allowed characters for the name?
  in_toto_args.add_argument("-n", "--name", type=str, required=True,
      help="Unique name for link metadata")

  # FIXME: This is not yet ideal.
  # What should we do with tokens like > or ; ?
  in_toto_args.add_argument("link_cmd", nargs="+",
    help="Link command to be executed with options and arguments")

  args = parser.parse_args()

  # Default to verbose
  log.setLevel(logging.INFO)

  in_toto_mock(args.name, args.link_cmd)

if __name__ == "__main__":
  main()
