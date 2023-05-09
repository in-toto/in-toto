#!/usr/bin/env python

# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""CLI to check local artifacts.
"""
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
from in_toto.runlib import in_toto_match_products as match_products

LOG = logging.getLogger(__name__)


def create_parser():
    """Create parser."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Check if local artifacts match products in passed link.",
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
        "-p",
        "--paths",
        type=str,
        required=False,
        nargs="+",
        metavar="<path>",
        help="file or directory paths to local artifacts. Default is CWD.",
    )

    parser.add_argument(
        "-e",
        "--exclude",
        required=False,
        metavar="<pattern>",
        nargs="+",
        help="gitignore-style patterns to exclude artifacts from matching.",
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
    only_products, not_in_products, differ = match_products(
        metadata.signed,
        paths=args.paths,
        exclude_patterns=args.exclude,
        lstrip_paths=args.lstrip_paths,
    )
    # raise Exception("test")
    if only_products or not_in_products or differ:
        if args.verbose:
            print("Local artifacts don't match products in passed link.")
            for name in only_products:
                print(f"Only in products: {name}")

            for name in not_in_products:
                print(f"Not in products: {name}")

            for name in differ:
                print(f"Hashes differ: {name}")

        sys.exit(1)

    if args.verbose:
        print("Local artifacts match products in passed link.")
    sys.exit(0)


if __name__ == "__main__":
    main()
