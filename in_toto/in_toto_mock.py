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
  Provides a command line interface for runlib.in_toto_mock.

<Return Codes>
  2 if an exception occurred during argument parsing
  1 if an exception occurred
  0 if no exception occurred

<Help>
usage: in-toto-mock [-h] --name <name> -- <command> [args]

A stripped down variant of 'in-toto-run' that can be used to create unsigned
link metadata for the passed command, recording all files in the current
working directory as materials and products.

This command should not be used to secure the supply chain but only to try
out the 'in-toto-run' command.

positional arguments:
  <command>             Command to be executed with options and arguments,
                        separated from 'in-toto-mock' options by double dash
                        '--'.

optional arguments:
  -h, --help            show this help message and exit

required named arguments:
  -n <name>, --name <name>
                        Name used to associate the resulting link metadata
                        with the corresponding step defined in an in-toto
                        layout.

examples:
  Generate link metadata 'foo' for the activity of creating file 'bar'.

    in-toto-mock --name foo -- touch bar

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
     formatter_class=argparse.RawDescriptionHelpFormatter,
      description="""
A stripped down variant of 'in-toto-run' that can be used to create unsigned
link metadata for the passed command, recording all files in the current
working directory as materials and products.

This command should not be used to secure the supply chain but only to try
out the 'in-toto-run' command.""")

  parser.usage = "%(prog)s [-h] --name <name> -- <command> [args]"

  parser.epilog = """
examples:
  Generate link metadata 'foo' for the activity of creating file 'bar'.

    {prog} --name foo -- touch bar

""".format(prog=parser.prog)


  named_args = parser.add_argument_group("required named arguments")

  # FIXME: Do we limit the allowed characters for the name?
  named_args.add_argument("-n", "--name", type=str, required=True,
      metavar="<name>", help=(
      "Name used to associate the resulting link metadata with the"
      " corresponding step defined in an in-toto layout."))

  # FIXME: This is not yet ideal.
  # What should we do with tokens like > or ; ?
  parser.add_argument("link_cmd", nargs="+", metavar="<command>",
      help=(
      "Command to be executed with options and arguments, separated from"
      " 'in-toto-mock' options by double dash '--'."))

  args = parser.parse_args()

  # in-toto-mock should not be used to secure the supply chain but only to try
  # out in-toto-run with max. user feedback, hence we set a verbose log level
  log.setLevel(logging.INFO)

  try:
    in_toto.runlib.in_toto_mock(args.name, args.link_cmd)

  except Exception as e:
    log.error("(in-toto-mock) {0}: {1}".format(type(e).__name__, e))
    sys.exit(1)

  sys.exit(0)


if __name__ == "__main__":
  main()
