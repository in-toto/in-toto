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
import unittest
import argparse
import in_toto.common_args


class TestArgparseActionGroupHelpers(unittest.TestCase):
  # pylint: disable=protected-access

  def setUp(self):
    """Create an empty parser and perform some basic assertions prior to
    testing parser action group (i.e. argument group) helper functions. """
    # Create empty argument parser
    self.parser = argparse.ArgumentParser()

    # Assert parser has the protected member "_action_groups" and it is a list
    # NOTE: argparse could remove this at any time without notice
    self.assertTrue(type(getattr(self.parser, "_action_groups", None)) == list) # pylint: disable=unidiomatic-typecheck

    # Assert default action groups with default titles' case and default order
    self.assertListEqual([group.title for group in self.parser._action_groups],
        ["positional arguments", "optional arguments"])


  def test_title_case_action_groups(self):
    """Test title_case_action_groups title cases action group titles. """
    # Make titles title-case (default is asserted in setUp)
    in_toto.common_args.title_case_action_groups(self.parser)

    # Assert successful title-casing
    self.assertListEqual([group.title for group in self.parser._action_groups],
        ["Positional Arguments", "Optional Arguments"])


  def  test_sort_action_groups(self):
    """Test sort_action_groups sorts action groups by custom title order. """
    # Create custom order for titles (default is asserted in setUp)
    custom_order = ["optional arguments", "positional arguments"]
    in_toto.common_args.sort_action_groups(
        self.parser, title_order=custom_order)
    # Assert successful re-ordering
    self.assertListEqual([group.title for group in self.parser._action_groups],
        custom_order)


    # Add custom group to parser that exists in most in-toto command line tools
    self.parser.add_argument_group("required named arguments")

    # Test default custom order of action groups titles (which are title-cased)
    in_toto.common_args.title_case_action_groups(self.parser)
    in_toto.common_args.sort_action_groups(self.parser)
    default_custom_order = ["Required Named Arguments", "Positional Arguments",
    "Optional Arguments"]

    # Assert successful(title-casing) re-ordering
    self.assertListEqual([group.title for group in self.parser._action_groups],
        default_custom_order)


if __name__ == "__main__":
  unittest.main()
