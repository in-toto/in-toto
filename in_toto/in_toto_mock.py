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

"""
import sys
import argparse
import logging
import in_toto.runlib
from in_toto.common_args import title_case_action_groups, sort_action_groups
from in_toto import __version__

# Command line interfaces should use in_toto base logger (c.f. in_toto.log)
LOG = logging.getLogger("in_toto")


def create_parser():
  """Parse arguments and call in_toto_mock. """
  parser = argparse.ArgumentParser(
     formatter_class=argparse.RawDescriptionHelpFormatter,
      description="""
in-toto-mock is a variant of 'in-toto-run' that can be used to create unsigned
link metadata, using defaults for many of the 'in-toto-run' arguments.
in-toto-mock verbosely executes the passed command, records all files in the
current working directory as materials and products, and generates a link file
under '<name>.link'.

This is useful for trying out how to generate a link without the need for a
key, or knowledge about all 'in-toto-run' arguments. It can also be used to
quickly generate link metadata, inspect it and sign it retroactively.

""")

  parser.usage = "%(prog)s [-h] --name <name> -- <command> [args]"

  parser.epilog = """EXAMPLE USAGE

Generate unsigned link metadata 'foo.link' for the activity of creating file
'bar', inspect it, and sign it with 'mykey'

  # Generate unsigned link
  {prog} --name foo -- touch bar
  # Inspect and/or update unsigned link metadata
  vi foo.link
  # Sign the link, attesting to its validity, and write it to
  # 'foo.<mykey keyid prefix>.link'.
  in-toto-sign -k mykey -f foo.link

""".format(prog=parser.prog)


  named_args = parser.add_argument_group("required named arguments")

  # FIXME: Do we limit the allowed characters for the name?
  named_args.add_argument("-n", "--name", type=str, required=True,
      metavar="<name>", help=(
      "name for the resulting link metadata file, which is written to"
      " '<name>.link'. It is also used to associate the link with a step"
      " defined in an in-toto layout."))

  # FIXME: This is not yet ideal.
  # What should we do with tokens like > or ; ?
  parser.add_argument("link_cmd", nargs="+", metavar="<command>",
      help=(
      "command to be executed. It is separated from named and optional"
      " arguments by a double dash '--'."))

  parser.add_argument('--version', action='version',
                      version='{} {}'.format(parser.prog, __version__))

  title_case_action_groups(parser)
  sort_action_groups(parser)

  return parser


def main():
  """Parse arguments and call in_toto_mock. """
  parser = create_parser()
  args = parser.parse_args()

  # in-toto-mock should not be used to secure the supply chain but only to try
  # out in-toto-run with max. user feedback, hence we set a verbose log level
  LOG.setLevel(logging.INFO)

  try:
    in_toto.runlib.in_toto_mock(args.name, args.link_cmd)

  except Exception as e:
    LOG.error("(in-toto-mock) {0}: {1}".format(type(e).__name__, e))
    sys.exit(1)

  sys.exit(0)


if __name__ == "__main__":
  main()
