#!/usr/bin/env python

# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""CLI to check local materials.
"""
# TODO: Remove with in-toto/in-toto#580
# pylint: disable=bad-indentation

import argparse
import logging
import sys

from in_toto.common_args import (
  LSTRIP_PATHS_ARGS,
  LSTRIP_PATHS_KWARGS,
  VERBOSE_ARGS,
  VERBOSE_KWARGS,
  sort_action_groups,
  title_case_action_groups,
)
from in_toto.models.metadata import Metadata
from in_toto.runlib import in_toto_check_materials as check_materials

LOG = logging.getLogger(__name__)


def create_parser():
    """Create parser."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Check if local materials match products in passed link.",
    )
    required = parser.add_argument_group("required named arguments")
    required.add_argument(
        "-l",
        "--link",
        type=str,
        required=True,
        metavar="<path>",
        help="path to link metadata file.",
    )
    parser.add_argument(
        "-m",
        "--materials",
        type=str,
        required=False,
        nargs="+",
        metavar="<path>",
        help="file or directory paths to local materials. Default is CWD.",
    )

    parser.add_argument(
        "-e",
        "--exclude",
        required=False,
        metavar="<pattern>",
        nargs="+",
        help="gitignore-style patterns to exclude materials from matching.",
    )

    parser.add_argument(*LSTRIP_PATHS_ARGS, **LSTRIP_PATHS_KWARGS)
    parser.add_argument(*VERBOSE_ARGS, **VERBOSE_KWARGS)

    title_case_action_groups(parser)
    sort_action_groups(parser)

    return parser


def main():
    """CLI."""
    parser = create_parser()
    args = parser.parse_args()

    metadata = Metadata.load(args.link)
    only_products, only_materials, differ = check_materials(
        metadata.signed,
        material_paths=args.materials,
        exclude_patterns=args.exclude,
        lstrip_paths=args.lstrip_paths,
    )
    # raise Exception("test")
    if only_products or only_materials or differ:
        if args.verbose:
            print("Local materials don't match products in passed link.")
            for name in only_products:
                print(f"Only in products: {name}")

            for name in only_materials:
                print(f"Only in materials: {name}")

            for name in differ:
                print(f"Hashes differ: {name}")

        sys.exit(1)

    if args.verbose:
        print("Local materials match products in passed link.")
    sys.exit(0)


if __name__ == "__main__":
    main()
