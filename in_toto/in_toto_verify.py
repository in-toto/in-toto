#!/usr/bin/env python
"""
<Program Name>
  in_toto_verify.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Oct 3, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides a command line interface that wraps the verification of
  in_toto final product.

  The actual verification is implemented in verifylib.

  Example Usage:
  ```
  in-toto-verify --layout <root.layout> --layout-keys <layout-key>
  ```

"""
import sys
import argparse
import in_toto.util
import in_toto.verifylib
import in_toto.log as log
from in_toto.models.layout import Layout

def _die(msg, exitcode=1):
  log.failing(msg)
  sys.exit(exitcode)

def in_toto_verify(layout_path, layout_key_paths):
  """Loads layout file and layout keys from disk and performs all in-toto
  verifications."""

  try:
    log.doing("load layout...")
    layout = Layout.read_from_file(layout_path)
  except Exception, e:
    _die("in load layout - %s" % e)

  try:
    log.doing("verify layout expiration")
    in_toto.verifylib.verify_layout_expiration(layout)
  except Exception, e:
    _die("in verify layout expiration - %s" % e)

  try:
    log.doing("load layout keys...")
    layout_key_dict = in_toto.util.import_rsa_public_keys_from_files_as_dict(
        layout_key_paths)
  except Exception, e:
    _die("in load layout keys - %s" % e)

  try:
    log.doing("verify layout signatures...")
    in_toto.verifylib.verify_layout_signatures(layout, layout_key_dict)
  except Exception, e:
    _die("in verify layout signatures - %s" % e)

  try:
    log.doing("load link metadata for steps...")
    step_link_dict = layout.import_step_metadata_from_files_as_dict()
  except Exception, e:
    _die("in load link metadata - %s" % e)

  try:
    log.doing("verify all step command alignments...")
    in_toto.verifylib.verify_all_steps_command_alignment(layout, step_link_dict)
  except Exception, e:
    _die("command alignments - %s" % e)

  try:
    log.doing("verify signatures for all links...")
    in_toto.verifylib.verify_all_steps_signatures(layout, step_link_dict)
  except Exception, e:
    _die("in verify link signatures - %s" % e)

  try:
    log.doing("run all inspections...")
    inspection_link_dict = in_toto.verifylib.run_all_inspections(layout)
  except Exception, e:
    _die("in run inspections - %s" % e)

  try:
    log.doing("verify all step matchrules...")
    in_toto.verifylib.verify_all_item_rules(layout.steps, step_link_dict)
  except Exception, e:
    _die("in verify all step matchrules - %s" % e)

  try:
    log.doing("verify all inspection matchrules...")
    in_toto.verifylib.verify_all_item_rules(layout.inspect, inspection_link_dict,
        step_link_dict)
  except Exception, e:
    _die("in verify all inspection matchrules - %s" % e)

  log.passing("all verification")

def main():

  parser = argparse.ArgumentParser(
      description="Verifies in-toto final product")

  # Whitespace padding to align with program name
  lpad = (len(parser.prog) + 1) * " "

  parser.usage = ("\n"
      "%(prog)s --layout <layout path>\n{0}"
               "--layout-keys (<layout pubkey path>,...)\n\n"
               .format(lpad))

  in_toto_args = parser.add_argument_group("in-toto options")

  in_toto_args.add_argument("-l", "--layout", type=str, required=True,
      help="Root layout to use for verification")

  in_toto_args.add_argument("-k", "--layout-keys", type=str, required=True,
    help="Key(s) to verify root layout signature (separated ',')")

  args = parser.parse_args()

  layout_key_paths = args.layout_keys.split(',')
  in_toto_verify(args.layout, layout_key_paths)

if __name__ == '__main__':
  main()
