#!/usr/bin/env python
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

  The implementation of the tasks can be found in runlib.

  Example Usage
  ```
  toto-run.py --step-name write-code --materials . --products . --key bob \
      -- vi foo.py
  ```

"""

import os
import sys
import argparse
import toto.util
import toto.runlib
import toto.log as log
from toto.models.link import Link

def _die(msg, exitcode=1):
  log.error(msg)
  sys.exit(exitcode)


def in_toto_start_record(step_name, key_path, material_list):
  """Load link signing private keys from disk, record passed materials,
  sign with key, store to disk as:
  .<step_name>.link-unfinished

  """
  try:
    log.doing("Start recording '{0}'...".format(step_name))
    key = toto.util.prompt_import_rsa_key_from_file(key_path)

    log.doing("record materials...")
    materials_dict = toto.runlib.record_artifacts_as_dict(material_list)

    log.doing("create preliminary link metadata...")
    link = toto.runlib.create_link_metadata(step_name, materials_dict)

    log.doing("sign metadata...")
    link.sign(key)

    log.doing("store metadata to '.{0}.link-unfinished'...".format(step_name))
    link.dump()

  except Exception, e:
    _die("in start record - %s" % e)


def in_toto_stop_record(step_name, key_path, product_list):
  """Load key, load .<step_name>.link-unfinished exists
  if exists, verify signature, record products, sign, dump, remove
  link-unfinished.

  """
  unfinished_fn = "." + str(step_name) + ".link-unfinished"
  try:
    log.doing("load link signing key...")
    key = toto.util.prompt_import_rsa_key_from_file(key_path)

    # There must be a file .<step_name>.link-unfinished in the current dir
    log.doing("load unfinished link file...")
    link_unfinished = Link.read_from_file(unfinished_fn)

    # The file must have been signed by the same key
    log.doing("verify unfinished link signature...")
    link_unfinished.verify_signatures(key)

    log.doing("record products...")
    link_unfinished.products = toto.runlib.record_artifacts_as_dict(product_list)

    log.doing("update signature...")
    link_unfinished.signatures = []
    link_unfinished.sign(key)

    log.doing("store metadata to file...")
    link.dump()

    log.doing("remove unfinished file...")
    os.remove(unfinished_fn)

  except Exception, e:
    _die("in stop record - %s" % e)

def in_toto_run(step_name, key_path, material_list, product_list,
    link_cmd_args, record_byproducts=False):
  """Load link signing private keys from disk and runs passed command, storing
  its materials, by-products and return value, and products into link metadata
  file. The link metadata file is signed and stored to disk. """
  try:
    log.doing("load link signing key...")
    key = toto.util.prompt_import_rsa_key_from_file(key_path)
  except Exception, e:
    _die("in load key - %s" % e)

  try:
    log.doing("record materials...")
    materials_dict = toto.runlib.record_artifacts_as_dict(material_list)
  except Exception, e:
    _die("in record materials - %s" % e)

  try:
    log.doing("run command...")
    byproducts, return_value = toto.runlib.execute_link(link_cmd_args,
        record_byproducts)
  except Exception, e:
    _die("in run command - %s" % e)

  try:
    log.doing("record products...")
    products_dict = toto.runlib.record_artifacts_as_dict(product_list)
  except Exception, e:
    _die("in record products - %s" % e)

  try:
    log.doing("create link metadata...")
    link = toto.runlib.create_link_metadata(step_name, materials_dict,
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
  parser.usage = ("\n"
      "%(prog)s  --step-name <unique step name>\n{0}"
               " --key <functionary private key path>\n{0}"
               "[--materials <filepath>[ <filepath> ...]]\n{0}"
               "[--products <filepath>[ <filepath> ...]]\n{0}"
               "[--record-byproducts] -- <cmd> [args]\n\n"

      "%(prog)s  --start-record --step-name <unique step name>\n{0}"
               " --key <functionary private key path>\n{0}"
               "[--materials <filepath>[ <filepath> ...]]\n\n"

      "%(prog)s --stop-record --step-name <unique step name>\n{0}"
               "--key <functionary private key path>\n{0}"
               "[--materials <filepath>[ <filepath> ...]]"
                .format((len(parser.prog) + 1) * " "))

  toto_args = parser.add_argument_group("Toto options")
  # FIXME: Name has to be unique!!! Where will we check this?
  # FIXME: Do we limit the allowed characters for the name?
  # FIXME: Should it be possible to add a path?
  toto_args.add_argument("-n", "--step-name", type=str, required=True,
      help="Unique name for link metadata")

  toto_args.add_argument("-m", "--materials", type=str, required=False,
      nargs='+', help="Files to record before link command execution")
  toto_args.add_argument("-p", "--products", type=str, required=False,
      nargs='+', help="Files to record after link command execution")

  # FIXME: Specifiy a format or choice of formats to use
  toto_args.add_argument("-k", "--key", type=str, required=True,
      help="Path to private key to sign link metadata")

  toto_args.add_argument("-b", "--record-byproducts", dest='record_byproducts',
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
