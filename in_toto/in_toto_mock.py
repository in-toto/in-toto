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
  the command line arguments.

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

import os
import sys
import argparse
from in_toto import (util, runlib, log)
from in_toto.models.link import Link
from in_toto.models.link import MOCK_FILENAME_FORMAT

def in_toto_mock(name, link_cmd_args):
  """
  <Purpose>
    Calls runlib.in_toto_run with current directory as material_list and
    product_list. Without signing key and record_byproducts as True.
    Writes the returned link to disk. And catches exceptions.

  <Arguments>
    name:
            A unique name to relate link metadata with a step defined in the
            layout.
    link_cmd_args:
            A list where the first element is a command and the remaining
            elements are arguments passed to that command.

  <Exceptions>
    SystemExit if any exception occurs

  <Side Effects>
    Writes newly created mock link metadata file to disk "<name>.link-mock"
    Calls sys.exit(1) if an exception is raised

  <Returns>
    None.
  """

  try:
    mock_link = runlib.in_toto_run(name, material_list=['.'],
        product_list=['.'], link_cmd_args=link_cmd_args, record_byproducts=True)
    mock_fn = MOCK_FILENAME_FORMAT.format(step_name=name)
    log.info("Storing mock link metadata to '{}'...".format(mock_fn))
    mock_link.dump(filename=mock_fn)

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

  # Turn on all the `log.info()` in the library
  log.logging.getLogger().setLevel(log.logging.INFO)

  in_toto_mock(args.name, args.link_cmd)

if __name__ == "__main__":
  main()
