# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  test_common_args.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Jan 16, 2020

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test in_toto/common_args.py

"""
# pylint: disable=protected-access

import argparse
import unittest

from in_toto.common_args import (
    KEY_PASSWORD_ARGS,
    KEY_PASSWORD_KWARGS,
    OPTS_TITLE,
    parse_password_and_prompt_args,
    sort_action_groups,
    title_case_action_groups,
)


class TestCommonArgs(unittest.TestCase):
    """Test CLI utils."""

    def test_parse_password_and_prompt_args(self):
        """Test parse -P/--password optional arg (nargs=?, const=True)."""
        parser = argparse.ArgumentParser()
        parser.add_argument(*KEY_PASSWORD_ARGS, **KEY_PASSWORD_KWARGS)

        # parameter list | expected result tuple, i.e password, prompt
        tests = [
            ([], (None, False)),
            (["--password"], (None, True)),
            (["--password", "123456"], ("123456", False)),
            (["-P"], (None, True)),
            (["-P", "123456"], ("123456", False)),
        ]

        for idx, (params, expected) in enumerate(tests):
            result = parse_password_and_prompt_args(parser.parse_args(params))
            self.assertTupleEqual(result, expected, "(row {})".format(idx))


class TestArgparseActionGroupHelpers(unittest.TestCase):
    """Test functions to hack cli output."""

    # pylint: disable=protected-access

    def setUp(self):
        """Create an empty parser and perform some basic assertions prior to
        testing parser action group (i.e. argument group) helper functions."""
        # Create empty argument parser
        self.parser = argparse.ArgumentParser()

        # Assert parser has the protected member "_action_groups" and it is a list
        # NOTE: argparse could remove this at any time without notice
        self.assertIsInstance(
            getattr(self.parser, "_action_groups", None), list
        )

        # Assert default action groups with default titles' case and default order
        self.assertListEqual(
            [group.title for group in self.parser._action_groups],
            ["positional arguments", OPTS_TITLE.lower()],
        )

    def test_title_case_action_groups(self):
        """Test title_case_action_groups title cases action group titles."""
        # Make titles title-case (default is asserted in setUp)
        title_case_action_groups(self.parser)

        # Assert successful title-casing
        self.assertListEqual(
            [group.title for group in self.parser._action_groups],
            ["Positional Arguments", OPTS_TITLE],
        )

    def test_sort_action_groups(self):
        """Test sort_action_groups sorts action groups by custom title order."""
        # Create custom order for titles (default is asserted in setUp)
        custom_order = [OPTS_TITLE.lower(), "positional arguments"]
        sort_action_groups(self.parser, title_order=custom_order)
        # Assert successful re-ordering
        self.assertListEqual(
            [group.title for group in self.parser._action_groups], custom_order
        )

        # Add custom group to parser that exists in most in-toto command line tools
        self.parser.add_argument_group("required named arguments")

        # Test default custom order of action groups titles (which are title-cased)
        title_case_action_groups(self.parser)
        sort_action_groups(self.parser)
        default_custom_order = [
            "Required Named Arguments",
            "Positional Arguments",
            OPTS_TITLE,
        ]

        # Assert successful(title-casing) re-ordering
        self.assertListEqual(
            [group.title for group in self.parser._action_groups],
            default_custom_order,
        )


if __name__ == "__main__":
    unittest.main()
