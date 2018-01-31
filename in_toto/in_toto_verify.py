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

  Exits with 0 if verification passes 1 if any exception is raised during
  verification, i.e. verification fails and 2 if incorrect arguments are passed
  to the command line tool.


  Example Usage:
  ```
  # Verify layout (path is "metadata/root.layout") with securesystemslib
  # layout key (path is "keys/owner.pub")
  in-toto-verify --layout metadata/root.layout --layout-keys keys/owner.pub

  # Verify layout (path is "metadata/root.layout") with GPG layout key
  # (keyid is 8465A1E2E0FB2B40ADB2478E18FB3F537E0C8A17) from gpg keyring
  # at "~/.gnupg"
  in-toto-verify --layout metadata/root.layout \
      --gpg 8465A1E2E0FB2B40ADB2478E18FB3F537E0C8A17 --gpg-home ~/.gnupg
  ```

"""
import sys
import argparse
import logging

import in_toto.util
from in_toto import verifylib
from in_toto.models.metadata import Metablock


# Command line interfaces should use in_toto base logger (c.f. in_toto.log)
log = logging.getLogger("in_toto")


def in_toto_verify(layout_path, layout_key_paths, layout_gpg_keyids, gpg_home):
  """
  <Purpose>
    Loads the layout metadata as Metablock object (containing a Layout object)
    and the signature verification keys from the passed paths and/or from
    layout_gpg_keyids, calls verifylib.in_toto_verify
    and handles exceptions.

    The layout has to be signed by the private key corresponding to each passed
    public key (path) or gpg key (keyid). If any of the signatures are missing
    or invalid verification fails.

  <Arguments>
    layout_path:
            Path to layout metadata file that is being verified.

    layout_key_paths:
            List of path(s) to project owner public key(s), used to verify the
            root layout's signature(s).

    layout_gpg_keyids:
            List of project owner GPG keyid(s), used to verify the root
            layout's signature(s).

    gpg_home:
            Path to GPG keyring (if not set the default keyring is used).

  <Exceptions>
    SystemExit if any exception occurs

  <Side Effects>
    Calls sys.exit(1) if an exception is raised

  <Returns>
    None.

  """
  try:
    log.info("Verifying software supply chain...")

    log.info("Loading layout...")
    layout = Metablock.load(layout_path)

    layout_key_dict = {}
    if layout_key_paths != None:
      log.info("Loading layout key(s)...")
      layout_key_dict.update(
          in_toto.util.import_rsa_public_keys_from_files_as_dict(
          layout_key_paths))

    if layout_gpg_keyids != None:
      log.info("Loading layout gpg key(s)...")
      layout_key_dict.update(
          in_toto.util.import_gpg_public_keys_from_keyring_as_dict(
          layout_gpg_keyids, gpg_home=gpg_home))

    verifylib.in_toto_verify(layout, layout_key_dict)

  except Exception as e:
    log.info("{0} - {1}".format(type(e).__name__, e))
    sys.exit(1)

def main():
  """Parse arguments and call in_toto_verify. """
  parser = argparse.ArgumentParser(
      description="Verifies in-toto final product")

  # Whitespace padding to align with program name
  lpad = (len(parser.prog) + 1) * " "

  parser.usage = ("\n"
      "%(prog)s --layout <layout path>\n{0}"
               "{{--layout-keys <filepath>[ <filepath> ...], "
               " --gpg <keyid> [ <keyid> ...]}} \n{0}"
               "[--gpg-home <path to gpg keyring>]\n{0}"
               "[--verbose | --quiet]\n\n"
               .format(lpad))

  in_toto_args = parser.add_argument_group("in-toto options")

  in_toto_args.add_argument("-l", "--layout", type=str, required=True,
      help="Root layout to use for verification")

  in_toto_args.add_argument("-k", "--layout-keys", type=str,
    nargs="+", help="Key(s) to verify root layout signature")

  parser.add_argument("-g", "--gpg", nargs="+",
      help=("GPG keyid to verify metadata root layout signature. "
      "(if set without argument, the default key is used)"))

  parser.add_argument("--gpg-home", dest="gpg_home", type=str,
      help="Path to GPG keyring (if not set the default keyring is used)")


  verbosity_args = parser.add_mutually_exclusive_group(required=False)
  verbosity_args.add_argument("-v", "--verbose", dest="verbose",
      help="Verbose execution.", action="store_true")

  verbosity_args.add_argument("-q", "--quiet", dest="quiet",
      help="Suppress all output.", action="store_true")


  args = parser.parse_args()

  log.setLevelVerboseOrQuiet(args.verbose, args.quiet)

  # For verifying at least one of --layout-keys or --gpg must be specified
  # Note: Passing both at the same time is possible.
  if (args.layout_keys == None) and (args.gpg == None):
    parser.print_help()
    parser.exit(2, "wrong arguments: specify at least one of "
      " `--layout-keys path [path ...]` or `--gpg id [id ...]`")

  in_toto_verify(args.layout, args.layout_keys, args.gpg, args.gpg_home)

if __name__ == "__main__":
  main()
