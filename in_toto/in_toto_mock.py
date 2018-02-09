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

<Arguments>
  name:
          A unique name to relate mock link metadata with a step defined
          in the layout.
  command:
          A list where the first element is a command and the remaining
          elements are arguments passed to that command.


<Return Codes>
  2 if an exception occurred during argument parsing
  1 if an exception occurred
  0 if no exception occurred

"""
import sys
import argparse
import logging
import in_toto.runlib

# Command line interfaces should use in_toto base logger (c.f. in_toto.log)
log = logging.getLogger("in_toto")



def main():
  """Parse arguments and call in_toto_mock. """
  parser = argparse.ArgumentParser(
      description="Executes link command and records metadata")

  parser.usage = "%(prog)s [-h] --name <unique step name> -- <command> [args]"

  named_args = parser.add_argument_group("required named arguments")

  # FIXME: Do we limit the allowed characters for the name?
  named_args.add_argument("-n", "--name", type=str, required=True,
      help="Unique name for link metadata", metavar="<unique step name>")

  # FIXME: This is not yet ideal.
  # What should we do with tokens like > or ; ?
  parser.add_argument("link_cmd", nargs="+", metavar="<command>",
    help="Link command to be executed with options and arguments")

  args = parser.parse_args()

  # in-toto-mock should NOT be used to secure the supply chain but only to
  # TRY out in-toto-run, with fewer command lines args and max. user feedback.
  log.setLevel(logging.INFO)

  try:
    in_toto.runlib.in_toto_mock(args.name, args.link_cmd)

  except Exception as e:
    log.error("(in-toto-mock) {0}: {1}".format(type(e).__name__, e))
    sys.exit(1)

  sys.exit(0)


if __name__ == "__main__":
  main()
