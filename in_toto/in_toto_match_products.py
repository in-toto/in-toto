#!/usr/bin/env python

# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  in_toto_match_products.py

<Author>
  Aditya Sirish A Yelgundhalli <aditya.sirish@nyu.edu>

<Started>
  Apr 17, 2023

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides a command line interface for verifylib.match_products.

<Return Codes>
  2 if an exception occurred during argument parsing
  1 if an exception occurred (verification failed)
  0 if no exception occurred (verification passed)

"""

import argparse
import logging
import sys
from in_toto.common_args import LSTRIP_PATHS_ARGS, LSTRIP_PATHS_KWARGS
from in_toto.models.metadata import Metadata
from in_toto.models.link import Link
from in_toto.verifylib import match_products


LOG = logging.getLogger("in_toto")


def create_parser():
  """Create and return configured ArgumentParser instance. """
  parser = argparse.ArgumentParser(
      formatter_class=argparse.RawDescriptionHelpFormatter,
      description="""
in-toto-match-products verifies local artifacts against the products of a
specified link metadata file.
"""
  )

  named_args = parser.add_argument_group("required named arguments")
  named_args.add_argument("-l", "--link", type=str, required=True,
      metavar="<path>",
      help="path to link metadata file to match products with.")

  named_args.add_argument("-a", "--artifacts", type=str, required=False,
      nargs='+', metavar="<path>",
      help="paths to files or directories to be matched to link's products.")

  parser.add_argument(*LSTRIP_PATHS_ARGS, **LSTRIP_PATHS_KWARGS)

  return parser


def main():
  """Parse arguments, load link from disk, and verify artifacts as passed in.
  """
  parser = create_parser()
  args = parser.parse_args()

  try:
    metadata = Metadata.load(args.link)
    match_products(metadata.signed, target_artifacts=args.artifacts,
      lstrip_paths=args.lstrip_paths)
  except Exception as e:
    LOG.error("(in-toto-match-products) {}: {}".format(type(e).__name__, e))
    sys.exit(1)

  sys.exit(0)

if __name__ == "__main__":
  main()
