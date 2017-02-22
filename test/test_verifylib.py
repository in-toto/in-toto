#!/usr/bin/env python

"""
<Program Name>
  test_verifylib.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Nov 07, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test verifylib functions.

"""

import os
import shutil
import copy
import tempfile
import unittest
from mock import patch
from datetime import datetime
from dateutil.relativedelta import relativedelta

import in_toto.settings
from in_toto.models.link import Link
from in_toto.models.layout import Step, Inspection, Layout
from in_toto.verifylib import (verify_delete_rule, verify_create_rule,
    verify_match_rule, verify_item_rules, verify_all_item_rules,
    verify_command_alignment, run_all_inspections, in_toto_verify,
    _raise_on_bad_retval)
from in_toto.exceptions import (RuleVerficationError,
    SignatureVerificationError, LayoutExpiredError, BadReturnValueError)
from in_toto.util import import_rsa_key_from_file


class Test_RaiseOnBadRetval(unittest.TestCase):
  """ Tests internal function that raises an exception if the passed
  "return_value" is not and integer and not zero. """

  def test_zero_return_value(self):
    """Don't raise exception on zero return value. """
    _raise_on_bad_retval(0)
    _raise_on_bad_retval(0, "command")

  def test_non_int_return_value(self):
    """Raise exception on non-int return value. """
    with self.assertRaises(BadReturnValueError):
      _raise_on_bad_retval("bad retval")
    with self.assertRaises(BadReturnValueError):
      _raise_on_bad_retval("bad retval", "bad command")

  def test_non_zero_return_value(self):
    """Raise exception on non-zero return value. """
    with self.assertRaises(BadReturnValueError):
      _raise_on_bad_retval(1)
    with self.assertRaises(BadReturnValueError):
      _raise_on_bad_retval(-1, "bad command")


class TestRunAllInspections(unittest.TestCase):
  """Test verifylib.run_all_inspections(layout)"""

  @classmethod
  def setUpClass(self):
    """
    Create layout with dummy inpsection.
    Create and change into temp test directory with dummy artifact."""

    # Create layout with one inspection
    self.layout = Layout.read({
      "_type": "layout",
      "steps": [],
      "inspect": [{
        "name": "touch-bar",
        "run": "touch bar",
      }]
    })

    # Create directory where the verification will take place
    self.working_dir = os.getcwd()
    self.test_dir = os.path.realpath(tempfile.mkdtemp())
    os.chdir(self.test_dir)
    open("foo", "w").write("foo")

  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp test directory. """
    os.chdir(self.working_dir)
    shutil.rmtree(self.test_dir)

  def test_inpsection_artifacts_with_base_path_ignored(self):
    """Create new dummy test dir and set as base path, must ignore. """
    ignore_dir = os.path.realpath(tempfile.mkdtemp())
    ignore_foo = os.path.join(ignore_dir, "ignore_foo")
    open(ignore_foo, "w").write("ignore foo")
    in_toto.settings.ARTIFACT_BASE_PATH = ignore_dir

    run_all_inspections(self.layout)
    link = Link.read_from_file("touch-bar.link")
    self.assertListEqual(link.materials.keys(), ["foo"])
    self.assertListEqual(sorted(link.products.keys()), sorted(["foo", "bar"]))

    in_toto.settings.ARTIFACT_BASE_PATH = None
    shutil.rmtree(ignore_dir)

  def test_inspection_fail_with_non_zero_retval(self):
    """Test fail run inspections with non-zero return value. """
    layout = Layout.read({
      "_type": "layout",
      "steps": [],
      "inspect": [{
        "name": "non-zero-inspection",
        "run": "expr 1 / 0",
      }]
    })
    with self.assertRaises(BadReturnValueError):
      run_all_inspections(layout)


class TestVerifyCommandAlignment(unittest.TestCase):
  """Test verifylib.verify_command_alignment(command, expected_command)"""

  def setUp(self):
    self.command = ["vi", "file1", "file2"]

  def test_commands_align(self):
    """Cmd and expected cmd are equal, passes. """
    expected_command = ["vi", "file1", "file2"]
    verify_command_alignment(self.command, expected_command)

  def test_commands_do_not_fully_align_log_warning(self):
    """Cmd and expected cmd differ slightly. """
    expected_command = ["/usr/bin/vi", "file1", "file2"]

    with patch("in_toto.verifylib.log") as mock_logging:
      verify_command_alignment(self.command, expected_command)
      mock_logging.warning.assert_called_with("Run command '{0}'"
          " differs from expected command '{1}'"
          .format(self.command, expected_command))

  def test_commands_do_not_align_at_all_log_warning(self):
    """Cmd and expected cmd differ completely. """
    expected_command = ["make install"]

    with patch("in_toto.verifylib.log") as mock_logging:
      verify_command_alignment(self.command, expected_command)
      mock_logging.warning.assert_called_with("Run command '{0}'"
          " differs from expected command '{1}'"
          .format(self.command, expected_command))


class TestVerifyDeleteRule(unittest.TestCase):
  """Test verifylib.verify_delete_rule(rule, artifact_queue) """

  def setUp(self):
    """ Setup artifact queues. """
    self.artifact_queue = ["foo"]
    self.artifact_queue_empty = []


  def test_fail_delete_file(self):
    """["DELETE", "foo"], matches foo (not deleted), fails. """

    rule = ["DELETE", "foo"]
    with self.assertRaises(RuleVerficationError):
      verify_delete_rule(rule, self.artifact_queue)


  def test_fail_delete_star(self):
    """["DELETE", "*"], matches * in non-empty queue (not deleted), fails. """

    rule = ["DELETE", "*"]
    with self.assertRaises(RuleVerficationError):
        verify_delete_rule(rule, self.artifact_queue)


  def test_pass_delete_file(self):
    """["DELETE", "bar"] does not match bar (deleted), passes. """

    rule = ["DELETE", "bar"]
    self.assertIsNone(
        verify_delete_rule(rule, self.artifact_queue))


  def test_pass_delete_star(self):
    """["DELETE", "*"], does not match * in empty queue (deleted), passes. """

    rule = ["DELETE", "*"]
    self.assertIsNone(
        verify_delete_rule(rule, self.artifact_queue_empty))


  def test_pass_ignore_case_keyword(self):
    """["delete", "bar"], ["DELETE", "bar"], ignores keyword case, passes. """

    rule1 = ["delete", "bar"]
    rule2 = ["DELETE", "bar"]
    self.assertIsNone(
        verify_delete_rule(rule1, self.artifact_queue))
    self.assertIsNone(
        verify_delete_rule(rule2, self.artifact_queue))





class TestVerifyCreateRule(unittest.TestCase):
  """Test verifylib.verify_create_rule(rule, artifact_queue) """

  def setUp(self):
    """ Setup artifact queues. """
    self.artifact_queue = ["foo"]
    self.artifact_queue_foostar = ["foo", "bar", "foobar"]
    self.artifact_queue_empty = []

  def test_fail_create_file(self):
    """["CREATE", "bar"], does not mach bar (not created), fails. """

    rule = ["CREATE", "bar"]
    with self.assertRaises(RuleVerficationError):
      verify_create_rule(rule, self.artifact_queue)


  def test_fail_create_star(self):
    """["CREATE", "*"], does not match * (nothing created), fails. """

    rule = ["CREATE", "*"]
    with self.assertRaises(RuleVerficationError):
        verify_create_rule(rule, self.artifact_queue_empty)


  def test_pass_create_file(self):
    """["CREATE", "foo"], matches foo (created), passes. """

    rule = ["CREATE", "foo"]
    self.assertListEqual(
      verify_create_rule(rule, self.artifact_queue), [])


  def test_pass_create_star(self):
    """["CREATE", "*"], matches * in non-empty queue (created), passes. """

    rule = ["CREATE", "*"]
    self.assertListEqual(
        verify_create_rule(rule, self.artifact_queue), [])


  def test_remove_foostar_from_artifact_queue(self):
    """["CREATE", "foo*"], matches foo* (created), passes. """

    rule = ["CREATE", "foo*"]
    self.assertListEqual(
        verify_create_rule(rule, self.artifact_queue_foostar), ["bar"])


  def test_pass_ignore_case_keyword(self):
    """["create", "bar"], ["CREATE", "bar"], ignores keyword case, passes. """

    rule1 = ["create", "foo"]
    rule2 = ["CREATE", "foo"]
    self.assertListEqual(
        verify_create_rule(rule1, self.artifact_queue), [])
    self.assertListEqual(
        verify_create_rule(rule2, self.artifact_queue), [])





class TestVerifyMatchRule(unittest.TestCase):
  """Test verifylib.verify_match_rule(rule, artifact_queue, artifacts, links) """

  def setUp(self):
    """Setup artifact queues, artifacts dictionary and Link dictionary. """

    # Dummy artifact hashes
    self.sha256_foo = \
        "d65165279105ca6773180500688df4bdc69a2c7b771752f0a46ef120b7fd8ec3"
    self.sha256_foobar = \
        "155c693a6b7481f48626ebfc545f05236df679f0099225d6d0bc472e6dd21155"
    self.sha256_bar = \
        "cfdaaf1ab2e4661952a9dec5e8fa3c360c1b06b1a073e8493a7c46d2af8c504b"
    self.sha256_barfoo = \
        "2036784917e49b7685c7c17e03ddcae4a063979aa296ee5090b5bb8f8aeafc5d"

    # Link dictionary containing dummy artifacts related to Steps the rule is
    # matched with (match target).
    materials = {
      "foo": {"sha256": self.sha256_foo},
      "foobar": {"sha256": self.sha256_foobar}
    }
    products = {
      "bar": {"sha256": self.sha256_bar},
      "barfoo": {"sha256": self.sha256_barfoo}
      }

    # Note: For simplicity the Links don't have all usually required fields set
    self.links = {
        "link-1" : Link(name="link-1", materials=materials, products=products),
    }


  def test_pass_match_material(self):
    """["MATCH", "MATERIAL", "foo", "FROM", "link-1"],
    source artifact foo and target material foo hashes match, passes. """

    rule = ["MATCH", "MATERIAL", "foo", "FROM", "link-1"]
    artifacts = {
      "foo": {"sha256": self.sha256_foo}
    }
    queue = artifacts.keys()
    self.assertListEqual(
        verify_match_rule(rule, queue, artifacts, self.links), [])


  def test_pass_match_product(self):
    """["MATCH", "PRODUCT", "bar", "FROM", "link-1"],
    source artifact bar and target product bar hashes match, passes. """

    rule = ["MATCH", "PRODUCT", "bar", "FROM", "link-1"]
    artifacts = {
      "bar": {"sha256": self.sha256_bar}
    }
    queue = artifacts.keys()
    self.assertListEqual(
        verify_match_rule(rule, queue, artifacts, self.links), [])


  def test_pass_match_material_as_name(self):
    """["MATCH", "MATERIAL", "dist/foo", "AS", "foo", "FROM", "link-1"],
    source artifact dist/foo and target material foo hashes match, passes. """

    rule = ["MATCH", "MATERIAL", "dist/foo", "AS", "foo", "FROM", "link-1"]
    artifacts = {
      "dist/foo": {"sha256": self.sha256_foo}
    }
    queue = artifacts.keys()
    self.assertListEqual(
        verify_match_rule(rule, queue, artifacts, self.links), [])


  def test_pass_match_product_as_name(self):
    """["MATCH", "PRODUCT", "dist/bar", "AS", "bar", "FROM", "link-1"],
    source artifact dist/bar and target product bar hahes match, passes. """

    rule = ["MATCH", "PRODUCT", "dist/bar", "AS", "bar", "FROM", "link-1"]
    artifacts = {
      "dist/bar": {"sha256": self.sha256_bar}
    }
    queue = artifacts.keys()
    self.assertListEqual(
        verify_match_rule(rule, queue, artifacts, self.links), [])


  def test_pass_match_material_star(self):
    """["MATCH", "MATERIAL", "foo*", "FROM", "link-1"],
    source artifacts foo* match target materials foo* hashes, passes. """

    rule = ["MATCH", "MATERIAL", "foo*", "FROM", "link-1"]
    artifacts = {
      "foo": {"sha256": self.sha256_foo},
      "foobar": {"sha256": self.sha256_foobar}
    }
    queue = artifacts.keys()
    self.assertListEqual(
        verify_match_rule(rule, queue, artifacts, self.links), [])


  def test_pass_match_product_star(self):
    """["MATCH", "PRODUCT", "bar*", "FROM", "link-1"],
    source artifacts bar* match target products bar* hashes, passes. """

    rule = ["MATCH", "PRODUCT", "bar*", "FROM", "link-1"]
    artifacts = {
      "bar": {"sha256": self.sha256_bar},
      "barfoo": {"sha256": self.sha256_barfoo}
    }
    queue = artifacts.keys()
    self.assertListEqual(
        verify_match_rule(rule, queue, artifacts, self.links), [])


  def test_pass_match_material_as_star(self):
    """["MATCH", "MATERIAL", "dist/*", "AS", "foo*", "FROM", "link-1"],
    source artifacts dist/* match target materials foo* hashes, passes. """

    rule = ["MATCH", "MATERIAL", "dist/*", "AS", "foo*", "FROM", "link-1"]
    artifacts = {
      "dist/foo": {"sha256": self.sha256_foo},
      "dist/foobar": {"sha256": self.sha256_foobar}
    }
    queue = artifacts.keys()
    self.assertListEqual(
        verify_match_rule(rule, queue, artifacts, self.links), [])


  def test_pass_match_product_as_star(self):
    """["MATCH", "PRODUCT", "dist/*", "AS", "bar*", "FROM", "link-1"],
    source artifacts dist/* match target products bar* hashes, passes. """

    rule = ["MATCH", "PRODUCT", "dist/*", "AS", "bar*", "FROM", "link-1"]
    artifacts = {
      "dist/bar": {"sha256": self.sha256_bar},
      "dist/barfoo": {"sha256": self.sha256_barfoo}
    }
    queue = artifacts.keys()
    self.assertListEqual(
        verify_match_rule(rule, queue, artifacts, self.links), [])


  def test_fail_pattern_matched_nothing_in_target_materials(self):
    """["MATCH", "MATERIAL", "bar", "FROM", "link-1"],
    pattern bar does not match any materials in target, fails. """

    rule = ["MATCH", "MATERIAL", "bar", "FROM", "link-1"]
    with self.assertRaises(RuleVerficationError):
      verify_match_rule(rule, [], [], self.links)


  def test_fail_pattern_matched_nothing_in_target_products(self):
    """["MATCH", "PRODUCT", "foo", "FROM", "link-1"],
    pattern foo does not match any products in target, fails. """

    rule = ["MATCH", "PRODUCT", "foo", "FROM", "link-1"]
    with self.assertRaises(RuleVerficationError):
      # Pass an empty artifacts queue and artifacts dictionary
      # to match nothing
      verify_match_rule(rule, [], [], self.links)


  def test_fail_target_hash_not_found_in_source_artifacts(self):
    """["MATCH", "MATERIAL", "foo", "FROM", "link-1"],
    no source artifact matches target material's hash, fails. """

    rule = ["MATCH", "MATERIAL", "foo", "FROM", "link-1"]
    artifacts = {
      "bar": {"sha256": self.sha256_bar},
    }
    queue = artifacts.keys()
    with self.assertRaises(RuleVerficationError):
      verify_match_rule(rule, queue, artifacts, self.links)


  def test_fail_hash_not_found_in_artifacts_queue(self):
    """["MATCH", "MATERIAL", "foo", "FROM", "link-1"],
    no source artifact still in queue matches target material's hash, fails. """

    rule = ["MATCH", "MATERIAL", "foo", "FROM", "link-1"]
    artifacts = {
      "foo": {"sha256": self.sha256_foo},
    }
    queue = []
    with self.assertRaises(RuleVerficationError):
      verify_match_rule(rule, queue, artifacts, self.links)


  def test_fail_hash_matched_but_wrong_name(self):
    """["MATCH", "MATERIAL", "foo", "FROM", "link-1"],
    no source artifact matches target material's hash and path pattern, fails. """

    rule = ["MATCH", "MATERIAL", "dist/foo", "AS", "foo", "FROM", "link-1"]
    artifacts = {
      "foo": {"sha256": self.sha256_foo},
    }
    queue = artifacts.keys()
    with self.assertRaises(RuleVerficationError):
      verify_match_rule(rule, queue, artifacts, self.links)





class TestVerifyItemRules(unittest.TestCase):
  """Test verifylib.verify_item_rules(item_name, rules, artifacts, links)"""

  def setUp(self):
    self.item_name = "test-item"
    self.sha256_foo = \
        "d65165279105ca6773180500688df4bdc69a2c7b771752f0a46ef120b7fd8ec3"
    self.sha256_bar = \
        "cfdaaf1ab2e4661952a9dec5e8fa3c360c1b06b1a073e8493a7c46d2af8c504b"

    self.artifacts = {
      "foo": {"sha256": self.sha256_foo},
      "bar": {"sha256": self.sha256_bar}
    }
    self.links = {
      "link-1": Link(name="link-1",
          materials={}, products={"foo": {"sha256": self.sha256_foo}})
    }


  def test_pass_with_rule_of_each_type(self):
    """Pass with list of rules of each rule type. """

    rules = [
      ["CREATE", "bar"],
      ["DELETE", "baz"],
      ["MATCH", "PRODUCT", "foo", "FROM", "link-1"]
    ]
    verify_item_rules(self.item_name, rules, self.artifacts, self.links)


  def test_fail_with_conflicting_rules(self):
    """Fail with artifact being matched by a match and by a create rule."""

    rules = [
      ["MATCH", "PRODUCT", "foo", "FROM", "link-1"],
      ["CREATE", "foo"]
    ]

    with self.assertRaises(RuleVerficationError):
      verify_item_rules(self.item_name, rules, self.artifacts, self.links)


  def test_fail_unmatched_artifacts(self):
    """Fail with unmatched artifacts after executing all rules. """

    rules = []
    with self.assertRaises(RuleVerficationError):
      verify_item_rules(self.item_name, rules, self.artifacts, {})





class TestVerifyAllItemRules(unittest.TestCase):
  """Test verifylib.verify_all_item_rules(items, links, target_links=None). """

  def setUp(self):
    """Create a dummy supply chain with two steps one inspection and the
    according link metadata:

    write-code (Step) ->  package (step) -> untar (Inspection)

    'write-code' creates an artifact foo
    'package' creates foo.tar.gz and deletes foo
    'untar' untars foo.tar.gz which results in foo.tar.gz and foo

    """

    self.sha256_foo = \
        "d65165279105ca6773180500688df4bdc69a2c7b771752f0a46ef120b7fd8ec3"
    self.sha256_foo_tar = \
        "93c3c35a039a6a3d53e81c5dbee4ebb684de57b7c8be11b8739fd35804a0e918"

    self.steps = [
        Step(name="write-code",
            product_matchrules=[
                ["CREATE", "foo"]
            ],
        ),
        Step(name="package",
            material_matchrules=[
                ["MATCH", "PRODUCT", "foo",
                    "AS", "foo", "FROM", "write-code"]
            ],
            product_matchrules=[
                ["CREATE", "foo.tar.gz"],
                ["DELETE", "foo"]
            ],
        )
    ]

    self.inspections = [
        Inspection(name="untar",
            material_matchrules=[
                ["MATCH", "PRODUCT", "foo.tar.gz", "FROM", "package"]
            ],
            product_matchrules=[
                ["MATCH", "PRODUCT", "dir/foo", "AS", "foo",
                    "FROM", "write-code"]
            ]
        )
    ]

    self.step_links = {
      "write-code" : Link(name="write-code",
          products={
              "foo": {
                  "sha256": self.sha256_foo
              }
          }
      ),
      "package" : Link(name="package",
          materials={
              "foo": {
                  "sha256": self.sha256_foo
              }
          },
          products={
              "foo.tar.gz": {
                  "sha256": self.sha256_foo_tar
              }
          }
      )
    }

    self.inspection_links = {
        "untar" : Link(name="untar",
            materials={
                "foo.tar.gz": {
                    "sha256": self.sha256_foo_tar
                }
            },
            products={
                "dir/foo": {
                    "sha256": self.sha256_foo
                },
            }
        )
    }

  def test_pass_verify_all_step_rules(self):
    """Pass rule verification for dummy supply chain Steps. """
    verify_all_item_rules(self.steps, self.step_links)


  def test_pass_verify_all_inspection_rules(self):
    """Pass rule verification for dummy supply chain Inspections. """
    verify_all_item_rules(self.inspections, self.inspection_links,
        self.step_links)


class TestInTotoVerify(unittest.TestCase):
  """
  Tests verifylib.in_toto_verify(layout_path, layout_key_paths).

  Uses in-toto demo supply chain link metadata files and basic layout for
  verification.

  Copies the basic layout for different test scenarios:
    - single-signed layout
    - double-signed layout
    - expired layout
    - layout with failing link rule
    - layout with failing step rule

  """
  @classmethod
  def setUpClass(self):
    """Creates and changes into temporary directory.
    Copies demo files to temp dir...
      - owner/functionary key pairs
      - *.link metadata files
      - layout template (not signed, no expiration date)
      - final product

    ...and dumps various layouts for different test scenarios
    """
    # Backup original cwd
    self.working_dir = os.getcwd()

    # Find demo files
    demo_files = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "demo_files")

    # Create and change into temporary directory
    self.test_dir = os.path.realpath(tempfile.mkdtemp())
    os.chdir(self.test_dir)

    # Copy demo files to temp dir
    for file in os.listdir(demo_files):
      shutil.copy(os.path.join(demo_files, file), self.test_dir)

    # Load layout template
    layout_template = Layout.read_from_file("demo.layout.template")

    # Store various layout paths to be used in tests
    self.layout_single_signed_path = "single-signed.layout"
    self.layout_double_signed_path = "double-signed.layout"
    self.layout_expired_path = "expired.layout"
    self.layout_failing_step_rule_path = "failing-step-rule.layout"
    self.layout_failing_inspection_rule_path = "failing-inspection-rule.layout"

    # Import layout signing keys
    alice = import_rsa_key_from_file("alice")
    bob = import_rsa_key_from_file("bob")
    self.alice_path = "alice.pub"
    self.bob_path = "bob.pub"

    # dump single signed layout
    layout = copy.deepcopy(layout_template)
    layout.sign(alice)
    layout.dump(self.layout_single_signed_path)

    # dump double signed layout
    layout = copy.deepcopy(layout_template)
    layout.sign(alice)
    layout.sign(bob)
    layout.dump(self.layout_double_signed_path)

    # dump expired layout
    layout = copy.deepcopy(layout_template)
    layout.expires = (datetime.today()
       + relativedelta(months=-1)).isoformat() + "Z"
    layout.sign(alice)
    layout.dump(self.layout_expired_path)

    # dump layout with failing step rule
    layout = copy.deepcopy(layout_template)
    layout.steps[0].material_matchrules.insert(0,
        ["MATCH", "PRODUCT", "does-not-exist", "FROM", "write-code"])
    layout.sign(alice)
    layout.dump(self.layout_failing_step_rule_path)

    # dump layout with failing inspection rule
    layout = copy.deepcopy(layout_template)
    layout.inspect[0].material_matchrules.insert(0,
        ["MATCH", "PRODUCT", "does-not-exist", "FROM", "write-code"])
    layout.sign(alice)
    layout.dump(self.layout_failing_inspection_rule_path)

  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp dir. """
    os.chdir(self.working_dir)
    shutil.rmtree(self.test_dir)

  def test_verify_passing(self):
    """Test pass verification of single-signed layout. """
    in_toto_verify(self.layout_single_signed_path, [self.alice_path])

  def test_verify_passing_double_signed_layout(self):
    """Test pass verification of double-signed layout. """
    in_toto_verify(self.layout_double_signed_path, [self.alice_path,
        self.bob_path])

  def test_verify_failing_layout_not_found(self):
    """Test fail verification for layout not found. """
    with self.assertRaises(IOError):
      in_toto_verify("missing.layout", [self.alice_path])

  def test_verify_failing_key_not_found(self):
    """Test fail verification with layout key not found. """
    with self.assertRaises(IOError):
      in_toto_verify(self.layout_single_signed_path, ["missing-key.pub"])

  def test_verify_failing_wrong_key(self):
    """Test fail verification with wrong layout key. """
    with self.assertRaises(SignatureVerificationError):
      in_toto_verify(self.layout_single_signed_path, [self.bob_path])

  def test_verify_failing_missing_key(self):
    """Test fail verification with missing layout key. """
    with self.assertRaises(SignatureVerificationError):
      in_toto_verify(self.layout_double_signed_path, [self.bob_path])

  def test_verify_failing_layout_expired(self):
    """Test fail verification with expired layout. """
    with self.assertRaises(LayoutExpiredError):
      in_toto_verify(self.layout_expired_path, [self.alice_path, self.bob_path])

  def test_verify_failing_link_metadata_files(self):
    """Test fail verification with link metadata files not found. """
    os.rename("package.2dc02526.link", "package.link.bak")
    with self.assertRaises(IOError):
      in_toto_verify(self.layout_single_signed_path, [self.alice_path])
    os.rename("package.link.bak", "package.2dc02526.link")

  def test_verify_failing_inspection_exits_non_zero(self):
    """FIXME implement raise exception on inspection fail. """
    pass

  def test_verify_failing_step_rules(self):
    """Test fail verification with failing step matchrule. """
    with self.assertRaises(RuleVerficationError):
      in_toto_verify(self.layout_failing_step_rule_path, [self.alice_path])

  def test_verify_failing_inspection_rules(self):
    """Test fail verification with failing inspection matchrule. """
    with self.assertRaises(RuleVerficationError):
      in_toto_verify(self.layout_failing_inspection_rule_path,
          [self.alice_path])

if __name__ == "__main__":
  unittest.main(buffer=False)
