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

import in_toto.user_settings
import in_toto.log as log
import in_toto.util
from in_toto import verifylib
from in_toto.models.metadata import Metablock

def in_toto_verify(layout_path, layout_key_paths):
  """
  <Purpose>
    Loads the layout metadata as Metablock object (containg a Layout object)
    and the signature verification keys from the passed paths,
    calls   verifylib.in_toto_verify   and handles exceptions.

  <Arguments>
    layout_path:
            Path to layout metadata file that is being verified.

    layout_key_paths:
            List of paths to project owner public keys, used to verify the
            layout's signature.

  <Exceptions>
    SystemExit if any exception occurs

  <Side Effects>
    Calls sys.exit(1) if an exception is raised

  <Returns>
    None.

  """
  try:
    log.info("Verifying software supply chain...")

    log.info("Reading layout...")
    layout = Metablock.load(layout_path)

    log.info("Reading layout key(s)...")
    layout_key_dict = in_toto.util.import_rsa_public_keys_from_files_as_dict(
        layout_key_paths)

    verifylib.in_toto_verify(layout, layout_key_dict)
  except Exception as e:
    log.fail_verification("{0} - {1}".format(type(e).__name__, e))
    sys.exit(1)

def main():
  """Parse arguments and call in_toto_verify. """
  parser = argparse.ArgumentParser(
      description="Verifies in-toto final product")

  # Whitespace padding to align with program name
  lpad = (len(parser.prog) + 1) * " "

  parser.usage = ("\n"
      "%(prog)s --layout <layout path>\n{0}"
               "--layout-keys <filepath>[ <filepath> ...]\n{0}"
               "[--verbose]\n\n"
               .format(lpad))

  in_toto_args = parser.add_argument_group("in-toto options")

  in_toto_args.add_argument("-l", "--layout", type=str, required=True,
      help="Root layout to use for verification")

  in_toto_args.add_argument("-k", "--layout-keys", type=str, required=True,
    nargs="+", help="Key(s) to verify root layout signature")

  in_toto_args.add_argument("-v", "--verbose", dest="verbose",
      help="Verbose execution.", default=False, action="store_true")

  args = parser.parse_args()

  # Turn on all the `log.info()` in the library
  if args.verbose:
    log.logging.getLogger().setLevel(log.logging.INFO)

  # Override defaults in settings.py with environment variables and RCfiles
  in_toto.user_settings.set_settings()

  in_toto_verify(args.layout, args.layout_keys)

if __name__ == "__main__":
  main()
