#!/usr/bin/env python
"""
<Program Name>
  in_toto_run.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  June 27, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides a command line interface which takes any link command of the software
  supply chain as input and wraps in_toto metadata recording.

  in_toto run options are separated from the command to be executed by
  a double dash.

  The implementation of the tasks can be found in runlib.

  Example Usage
  ```
  in-toto-run --step-name write-code --materials . --products . --key bob \
      -- vi foo.py
  ```

"""

import os
import sys
import argparse
import in_toto.util
import in_toto.runlib
import in_toto.log as log
from in_toto.models.link import Link

def _die(msg, exitcode=1):
  log.error(msg)
  sys.exit(exitcode)


def in_toto_run(step_name, key_path, material_list, product_list,
    link_cmd_args, record_byproducts=False):
  """Load link signing private keys from disk and runs passed command, storing
  its materials, by-products and return value, and products into link metadata
  file. The link metadata file is signed and stored to disk. """
  try:
    log.doing("load link signing key...")
    key = in_toto.util.prompt_import_rsa_key_from_file(key_path)
  except Exception, e:
    _die("in load key - %s" % e)

  try:
    log.doing("record materials...")
    materials_dict = in_toto.runlib.record_artifacts_as_dict(material_list)
  except Exception, e:
    _die("in record materials - %s" % e)

  try:
    log.doing("run command...")
    byproducts, return_value = in_toto.runlib.execute_link(link_cmd_args,
        record_byproducts)
  except Exception, e:
    _die("in run command - %s" % e)

  try:
    log.doing("record products...")
    products_dict = in_toto.runlib.record_artifacts_as_dict(product_list)
  except Exception, e:
    _die("in record products - %s" % e)

  try:
    log.doing("create link metadata...")
    link = in_toto.runlib.create_link_metadata(step_name, materials_dict,
        products_dict, link_cmd_args, byproducts, return_value)
  except Exception, e:
    raise e

  try:
    log.doing("sign metadata...")
    link.sign(key)
  except Exception, e:
    _die("in sign metadata - %s" % e)

  try:
    log.doing("store metadata...")
    link.dump()
  except Exception, e:
    _die("in store metadata - %s" % e)

def main():
  parser = argparse.ArgumentParser(
      description="Executes link command and records metadata")
  # Whitespace padding to align with program name
  lpad = (len(parser.prog) + 1) * " "

  parser.usage = ("\n"
      "%(prog)s  --step-name <unique step name>\n{0}"
               " --key <functionary private key path>\n{0}"
               "[--materials <filepath>[ <filepath> ...]]\n{0}"
               "[--products <filepath>[ <filepath> ...]]\n{0}"
               "[--record-byproducts] -- <cmd> [args]\n\n"
               .format(lpad))

  in_toto_args = parser.add_argument_group("in-toto options")
  # FIXME: Name has to be unique!!! Where will we check this?
  # FIXME: Do we limit the allowed characters for the name?
  in_toto_args.add_argument("-n", "--step-name", type=str, required=True,
      help="Unique name for link metadata")

  in_toto_args.add_argument("-m", "--materials", type=str, required=False,
      nargs='+', help="Files to record before link command execution")
  in_toto_args.add_argument("-p", "--products", type=str, required=False,
      nargs='+', help="Files to record after link command execution")

  in_toto_args.add_argument("-k", "--key", type=str, required=True,
      help="Path to private key to sign link metadata (PEM)")

  in_toto_args.add_argument("-b", "--record-byproducts", dest='record_byproducts',
      help="If set redirects stdout/stderr and stores to link metadata",
      default=False, action='store_true')

  link_args = parser.add_argument_group("Link command")
  # FIXME: This is not yet ideal.
  # What should we do with tokens like > or ; ?
  link_args.add_argument("link_cmd", nargs="+",
    help="Link command to be executed with options and arguments")

  args = parser.parse_args()

  in_toto_run(args.step_name, args.key, args.materials, args.products,
      args.link_cmd, args.record_byproducts)

if __name__ == '__main__':
  main()
