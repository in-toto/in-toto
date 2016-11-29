#!/usr/bin/env python
"""
<Program Name>
  in_toto_record.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Nov 28, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides a command line interface to start and stop in-toto link metadata
  recording.

  start
    Takes a step name, a functionary's signing key and optional
    material paths.
    Creates a temporary link file containing the file hashes of the passed
    materials and signs it with the functionary's key under
    .<step name>.link-unfinished

  stop
    Takes a step name, a functionary's signing key and optional
    product paths.
    Expects a .<step name>.link-unfinished in the current directory signed by
    the functionary's signing key, adds the file hashes of the passed products,
    updates the signature and renames the file  .<step name>.link-unfinished
    to <step name>.link


  The implementation of the tasks can be found in runlib.

  Example Usage
  ```
  in_toto_record.py start --step-name edit-files --materials . --key bob
  # Edit files manually ...
  in_toto_record.py stop --step-name edit-files --products . --key bob
  ```

"""
import os
import sys
import argparse
import toto.util
from toto import runlib
from toto import log
from toto.models.link import Link


def in_toto_record_start(step_name, key_path, material_list):
  """
  <Purpose>
    Starts creating link metadata for a multi-part in-toto step. I.e.
    loads link signing private key from disk, records passed materials, creates
    link meta data object from it, signs it with loaded key and stores it to
    disk as ".<step_name>.link-unfinished".

  <Arguments>
    step_name:
            A unique name to relate link metadata with a step defined in the
            layout.
    key_path:
            Path to private key to sign link metadata (PEM).
    material_list:
            List of file or directory paths that should be recorded as
            materials.

  <Exceptions>
    None.

  <Side Effects>
    Loads private key from disk
    Creates a file with  name ".<step_name>.link-unfinished"
    Calls sys.exit(1) if an exception is raised

  <Returns>
    Link object (unfinished)

  """

  unfinished_fn = "." + str(step_name) + ".link-unfinished"

  try:
    log.doing("Start recording '{0}'...".format(step_name))
    key = toto.util.prompt_import_rsa_key_from_file(key_path)

    log.doing("record materials...")
    materials_dict = runlib.record_artifacts_as_dict(material_list)

    log.doing("create preliminary link metadata...")
    link = runlib.create_link_metadata(step_name, materials_dict)

    log.doing("sign metadata...")
    link.sign(key)

    log.doing("store metadata to '{0}'...".format(unfinished_fn))
    link.dump(unfinished_fn)

    return link

  except Exception, e:
    log.error("in start record - %s" % e)
    sys.exit(1)

def in_toto_record_stop(step_name, key_path, product_list):
  """
  <Purpose>
    Finishes creating link metadata for a multi-part in-toto step.
    Loads signing key and unfinished link metadata file from disk, verifies
    that the file was signed with the key, records products, updates unfinished
    Link object (products and signature), removes unfinished link file from and
    stores new link file to disk.

  <Arguments>
    step_name:
            A unique name to relate link metadata with a step defined in the
            layout.
    key_path:
            Path to private key to verify unfinished link metadata and
            sign finished link metadata (PEM).
    product_list:
            List of file or directory paths that should be recorded as products.

  <Exceptions>
    Exception if signature fails
    IOException if file ".<step_name>.link-unfinished" can't be read

  <Side Effects>
    Loads private key from disk
    Writes link file to disk "<step_name>.link"
    Remvoes unfinished link file ".<step_name>.link-unfinished" from disk
    Calls sys.exit(1) if an exception is raised

  <Returns>
    Link object

  """

  unfinished_fn = "." + str(step_name) + ".link-unfinished"

  try:
    log.doing("load link signing key...")
    key = toto.util.prompt_import_rsa_key_from_file(key_path)
    keydict = {key["keyid"] : key}

    # There must be a file .<step_name>.link-unfinished in the current dir
    log.doing("load unfinished link file...")
    link = Link.read_from_file(unfinished_fn)
    # The unfinished link file must have been signed by the same key

    log.doing("verify unfinished link signature...")
    link.verify_signatures(keydict)

    log.doing("record products...")
    link.products = runlib.record_artifacts_as_dict(product_list)

    log.doing("update signature...")
    link.signatures = []
    link.sign(key)

    log.doing("store metadata to file...")
    link.dump()

    log.doing("remove unfinished file...")
    os.remove(unfinished_fn)

    return link

  except Exception, e:
    log.error("in stop record - %s" % e)
    sys.exit(1)



def main():
  parser = argparse.ArgumentParser(
      description="Starts or stops link metadata recording")

  subparsers = parser.add_subparsers(dest="command")

  subparser_start = subparsers.add_parser('start')
  subparser_stop = subparsers.add_parser('stop')

  # Whitespace padding to align with program name
  lpad = (len(parser.prog) + 1) * " "
  parser.usage = ("\n"
      "%(prog)s  --step-name <unique step name>\n{0}"
               " --key <functionary private key path>\n"
      "Commands:\n{0}"
               "start [--materials <filepath>[ <filepath> ...]]\n{0}"
               "stop  [--products <filepath>[ <filepath> ...]]\n"
               .format(lpad))

  in_toto_args = parser.add_argument_group("Toto options")
  # FIXME: Name has to be unique!!! Where will we check this?
  # FIXME: Do we limit the allowed characters for the name?
  in_toto_args.add_argument("-n", "--step-name", type=str, required=True,
      help="Unique name for link metadata")

  in_toto_args.add_argument("-k", "--key", type=str, required=True,
      help="Path to private key to sign link metadata (PEM)")

  subparser_start.add_argument("-m", "--materials", type=str, required=False,
      nargs='+', help="Files to record before link command execution")

  subparser_stop.add_argument("-p", "--products", type=str, required=False,
      nargs='+', help="Files to record after link command execution")

  args = parser.parse_args()

  if args.command == "start":
    in_toto_record_start(args.step_name, args.key, args.materials)
  elif args.command == "stop":
    in_toto_record_stop(args.step_name, args.key, args.products)

if __name__ == '__main__':
  main()
