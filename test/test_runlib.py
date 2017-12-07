#!/usr/bin/env python

"""
<Program Name>
  test_runlib.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Dec 01, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test runlib functions.

"""

import os
import unittest
import shutil
import tempfile

import in_toto.settings
import in_toto.exceptions
from in_toto.models.metadata import Metablock
from in_toto.exceptions import SignatureVerificationError
from in_toto.runlib import (in_toto_run, in_toto_record_start,
    in_toto_record_stop, record_artifacts_as_dict, _apply_exclude_patterns)
from in_toto.util import (generate_and_write_rsa_keypair,
    prompt_import_rsa_key_from_file)
from in_toto.models.link import (UNFINISHED_FILENAME_FORMAT, FILENAME_FORMAT)

import securesystemslib.formats
import securesystemslib.exceptions

class Test_ApplyExcludePatterns(unittest.TestCase):
  """Test _apply_exclude_patterns(names, exclude_patterns) """

  def test_apply_exclude_explict(self):
    names = ["foo", "bar", "baz"]
    patterns = ["foo", "bar"]
    expected = ["baz"]
    result = _apply_exclude_patterns(names, patterns)
    self.assertListEqual(sorted(result), sorted(expected))

  def test_apply_exclude_all(self):
    names = ["foo", "bar", "baz"]
    patterns = ["*"]
    expected = []
    result = _apply_exclude_patterns(names, patterns)
    self.assertListEqual(sorted(result), sorted(expected))

  def test_apply_exclude_multiple_star(self):
    names = ["foo", "bar", "baz"]
    patterns = ["*a*"]
    expected = ["foo"]
    result = _apply_exclude_patterns(names, patterns)
    self.assertListEqual(result, expected)

  def test_apply_exclude_question_mark(self):
    names = ["foo", "bazfoo", "barfoo"]
    patterns = ["ba?foo"]
    expected = ["foo"]
    result = _apply_exclude_patterns(names, patterns)
    self.assertListEqual(result, expected)

  def test_apply_exclude_seq(self):
    names = ["baxfoo", "bazfoo", "barfoo"]
    patterns = ["ba[xz]foo"]
    expected = ["barfoo"]
    result = _apply_exclude_patterns(names, patterns)
    self.assertListEqual(result, expected)

  def test_apply_exclude_neg_seq(self):
    names = ["baxfoo", "bazfoo", "barfoo"]
    patterns = ["ba[!r]foo"]
    expected = ["barfoo"]
    result = _apply_exclude_patterns(names, patterns)
    self.assertListEqual(result, expected)


class TestRecordArtifactsAsDict(unittest.TestCase):
  """Test record_artifacts_as_dict(artifacts). """

  @classmethod
  def setUpClass(self):
    """Create and change into temp test directory with dummy artifacts.
    |-- bar
    |-- foo
    `-- subdir
        |-- foosub1
        |-- foosub2
        `-- subsubdir
            `-- foosubsub
    """

    self.working_dir = os.getcwd()

    # Backup and clear user set exclude patterns and base path
    self.artifact_exclude_orig = in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS
    self.artifact_base_path_orig = in_toto.settings.ARTIFACT_BASE_PATH
    in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS = []
    in_toto.settings.ARTIFACT_BASE_PATH = None

    # mkdtemp uses $TMPDIR, which might contain a symlink
    # but we want the absolute location instead
    self.test_dir = os.path.realpath(tempfile.mkdtemp())
    os.chdir(self.test_dir)

    open("foo", "w").write("foo")
    open("bar", "w").write("bar")

    os.mkdir("subdir")
    os.mkdir("subdir/subsubdir")
    open("subdir/foosub1", "w").write("foosub")
    open("subdir/foosub2", "w").write("foosub")
    open("subdir/subsubdir/foosubsub", "w").write("foosubsub")

    # Add dead symlinks on each level, they should be excluded
    os.symlink("this/file/does/not/exist", "deadlink")
    os.symlink("this/file/does/not/exist", "subdir/deadlink")
    os.symlink("this/file/does/not/exist", "subdir/subsubdir/deadlink")

  @classmethod
  def tearDownClass(self):
    """Change back to working dir, remove temp directory, restore settings. """
    os.chdir(self.working_dir)
    shutil.rmtree(self.test_dir)
    in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS = self.artifact_exclude_orig
    in_toto.settings.ARTIFACT_BASE_PATH = self.artifact_base_path_orig

  def tearDown(self):
    """Clear the ARTIFACT_EXLCUDES after every test. """
    in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS = []
    in_toto.settings.ARTIFACT_BASE_PATH = None

  def test_bad_base_path_setting(self):
    """Raise exception with bogus base path settings. """
    for setting in ["path/does/not/exist", 12345, True]:
      in_toto.settings.ARTIFACT_BASE_PATH = setting
      with self.assertRaises(in_toto.exceptions.SettingsError):
        print setting
        record_artifacts_as_dict(["."])

  def test_base_path_is_child_dir(self):
    """Test path of recorded artifacts and cd back with child as base."""
    in_toto.settings.ARTIFACT_BASE_PATH = "subdir"
    artifacts_dict = record_artifacts_as_dict(["."])
    self.assertListEqual(sorted(artifacts_dict.keys()),
        sorted(["foosub1", "foosub2", "subsubdir/foosubsub"]))
    self.assertEquals(os.getcwd(), self.test_dir)

  def test_base_path_is_parent_dir(self):
    """Test path of recorded artifacts and cd back with parent as base. """
    in_toto.settings.ARTIFACT_BASE_PATH = ".."
    os.chdir("subdir/subsubdir")
    artifacts_dict = record_artifacts_as_dict(["."])
    self.assertListEqual(sorted(artifacts_dict.keys()),
        sorted(["foosub1", "foosub2", "subsubdir/foosubsub"]))
    self.assertEquals(os.getcwd(),
        os.path.join(self.test_dir, "subdir/subsubdir"))
    os.chdir(self.test_dir)

  def test_empty_artifacts_list_record_nothing(self):
    """Empty list passed. Return empty dict. """
    self.assertDictEqual(record_artifacts_as_dict([]), {})

  def test_not_existing_artifacts_in_list_record_nothing(self):
    """List with not existing artifact passed. Return empty dict. """
    self.assertDictEqual(record_artifacts_as_dict(["baz"]), {})

  def test_record_dot_check_files_hash_dict_schema(self):
    """Traverse dir and subdirs. Record three files. """
    artifacts_dict = record_artifacts_as_dict(["."])

    for key, val in artifacts_dict.iteritems():
      securesystemslib.formats.HASHDICT_SCHEMA.check_match(val)

    self.assertListEqual(sorted(artifacts_dict.keys()),
      sorted(["foo", "bar", "subdir/foosub1", "subdir/foosub2",
          "subdir/subsubdir/foosubsub"]))

  def test_record_files_and_subdirs(self):
    """Explicitly record files and subdirs. """
    artifacts_dict = record_artifacts_as_dict(["foo", "subdir"])

    for key, val in artifacts_dict.iteritems():
      securesystemslib.formats.HASHDICT_SCHEMA.check_match(val)

    self.assertListEqual(sorted(artifacts_dict.keys()),
      sorted(["foo", "subdir/foosub1", "subdir/foosub2",
          "subdir/subsubdir/foosubsub"]))

  def test_record_dot_exclude_star_foo_star_from_recording(self):
    """Traverse dot. Exclude pattern. Record one file. """
    in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS = ["*foo*"]
    artifacts_dict = record_artifacts_as_dict(["."])

    securesystemslib.formats.HASHDICT_SCHEMA.check_match(artifacts_dict["bar"])
    self.assertListEqual(artifacts_dict.keys(), ["bar"])

  def test_exclude_subdir(self):
    """Traverse dot. Exclude subdir (and subsubdir). """
    in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS = ["*subdir"]
    artifacts_dict = record_artifacts_as_dict(["."])
    self.assertListEqual(sorted(artifacts_dict.keys()), sorted(["bar", "foo"]))

  def test_exclude_files_in_subdir(self):
    """Traverse dot. Exclude files in subdir but not subsubdir. """
    in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS = ["*foosub?"]
    artifacts_dict = record_artifacts_as_dict(["."])
    self.assertListEqual(sorted(artifacts_dict.keys()),
      sorted(["bar", "foo", "subdir/subsubdir/foosubsub"]))

  def test_exclude_subsubdir(self):
    """Traverse dot. Exclude subsubdir. """
    in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS = ["*subsubdir"]
    artifacts_dict = record_artifacts_as_dict(["."])

    for key, val in artifacts_dict.iteritems():
      securesystemslib.formats.HASHDICT_SCHEMA.check_match(val)

    self.assertListEqual(sorted(artifacts_dict.keys()),
        sorted(["foo", "bar", "subdir/foosub1", "subdir/foosub2"]))

  def test_bad_artifact_exclude_patterns_setting(self):
    """Raise exception with bogus artifact exclude patterns settings. """
    for setting in ["not a list of settings", 12345, True]:
      in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS = setting
      with self.assertRaises(in_toto.exceptions.SettingsError):
        print setting
        record_artifacts_as_dict(["."])


class TestInTotoRun(unittest.TestCase):
  """"
  Tests runlib.in_toto_run() with different arguments

  Calls in_toto_run library funtion inside of a temporary directory that
  contains a test artifact and a test keypair

  If the function does not fail it will dump a test step link metadata file
  to the temp dir which is removed after every test.

  """

  @classmethod
  def setUpClass(self):
    """Create and change into temporary directory, generate key pair and dummy
    material, read key pair. """

    self.working_dir = os.getcwd()

    self.test_dir = tempfile.mkdtemp()
    os.chdir(self.test_dir)

    self.step_name = "test_step"
    self.key_path = "test_key"
    generate_and_write_rsa_keypair(self.key_path)
    self.key = prompt_import_rsa_key_from_file(self.key_path)
    self.key_pub = prompt_import_rsa_key_from_file(self.key_path + ".pub")

    self.test_artifact = "test_artifact"
    open(self.test_artifact, "w").close()

  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp test directory. """
    os.chdir(self.working_dir)
    shutil.rmtree(self.test_dir)

  def tearDown(self):
    """Remove link file if it was created. """
    try:
      os.remove(FILENAME_FORMAT.format(step_name=self.step_name, keyid=self.key["keyid"]))
    except OSError:
      pass

  def test_in_toto_run_verify_signature(self):
    """Successfully run, verify signed metadata. """
    link = in_toto_run(self.step_name, None, None,
        ["echo", "test"], True, self.key)
    link.verify_signatures({self.key["keyid"] : self.key})

  def test_in_toto_run_no_signature(self):
    """Successfully run, verify empty signature field. """
    link = in_toto_run(self.step_name, None, None, ["echo", "test"])
    self.assertFalse(len(link.signatures))

  def test_in_toto_run_with_byproduct(self):
    """Successfully run, verify recorded byproduct. """
    link = in_toto_run(self.step_name, None, None, ["echo", "test"],
        record_streams=True)
    self.assertTrue("test" in link.signed.byproducts.get("stdout"))

  def test_in_toto_run_without_byproduct(self):
    """Successfully run, verify byproduct is not recorded. """
    link = in_toto_run(self.step_name, None, None, ["echo", "test"],
        record_streams=False)
    self.assertFalse(len(link.signed.byproducts.get("stdout")))

  def test_in_toto_run_compare_dumped_with_returned_link(self):
    """Successfully run, compare dumped link is equal to returned link. """
    link = in_toto_run(self.step_name, [self.test_artifact],
        [self.test_artifact], ["echo", "test"], True, self.key)
    link_dump = Metablock.load(
        FILENAME_FORMAT.format(step_name=self.step_name, keyid=self.key["keyid"]))
    self.assertEquals(repr(link), repr(link_dump))

  def test_in_toto_run_verify_recorded_artifacts(self):
    """Successfully run, verify properly recorded artifacts. """
    link = in_toto_run(self.step_name, [self.test_artifact],
        [self.test_artifact], ["echo", "test"])
    self.assertEqual(link.signed.materials.keys(),
        link.signed.products.keys(), [self.test_artifact])

  def test_in_toto_run_verify_workdir(self):
    """Successfully run, verify cwd. """
    link = in_toto_run(self.step_name, [], [], ["echo", "test"])
    self.assertEquals(link.signed.environment["workdir"], os.getcwd())

  def test_in_toto_bad_signing_key_format(self):
    """Fail run, passed key is not properly formatted. """
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      in_toto_run(self.step_name, None, None,
          ["echo", "test"], True, "this-is-not-a-key")

  def test_in_toto_wrong_key(self):
    """Fail run, passed key is a public key. """
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      in_toto_run(self.step_name, None, None,
          ["echo", "test"], True, self.key_pub)

class TestInTotoRecordStart(unittest.TestCase):
  """"Test in_toto_record_start(step_name, key, material_list). """

  @classmethod
  def setUpClass(self):
    """Create and change into temporary directory, generate key pair and dummy
    material, read key pair. """
    self.working_dir = os.getcwd()

    self.test_dir = tempfile.mkdtemp()
    os.chdir(self.test_dir)

    self.key_path = "test_key"
    generate_and_write_rsa_keypair(self.key_path)
    self.key = prompt_import_rsa_key_from_file(self.key_path)

    self.step_name = "test_step"
    self.link_name_unfinished = UNFINISHED_FILENAME_FORMAT.format(step_name=self.step_name, keyid=self.key["keyid"])

    self.test_material= "test_material"
    open(self.test_material, "w").close()

  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp test directory. """
    os.chdir(self.working_dir)
    shutil.rmtree(self.test_dir)

  def test_UNFINISHED_FILENAME_FORMAT(self):
    """Test if the unfinished filname format. """
    self.assertTrue(self.link_name_unfinished ==
        ".{}.{:.8}.link-unfinished".format(self.step_name, self.key["keyid"]))

  def test_create_unfinished_metadata_with_expected_material(self):
    """Test record start creates metadata with expected material. """
    in_toto_record_start(
        self.step_name, [self.test_material], self.key)
    link = Metablock.load(self.link_name_unfinished)
    self.assertEquals(link.signed.materials.keys(), [self.test_material])
    os.remove(self.link_name_unfinished)

  def test_create_unfininished_metadata_verify_signature(self):
    """Test record start creates metadata with expected signature. """
    in_toto_record_start(
        self.step_name, [self.test_material], self.key)
    link = Metablock.load(self.link_name_unfinished)
    link.verify_signatures({self.key["keyid"] : self.key})
    os.remove(self.link_name_unfinished)


class TestInTotoRecordStop(unittest.TestCase):
  """"Test in_toto_record_stop(step_name, key, product_list). """

  @classmethod
  def setUpClass(self):
    """Create and change into temporary directory, generate two key pairs
    and dummy product. """
    self.working_dir = os.getcwd()

    self.test_dir = tempfile.mkdtemp()
    os.chdir(self.test_dir)

    self.key_path = "test-key"
    self.key_path2 = "test-key2"
    generate_and_write_rsa_keypair(self.key_path)
    generate_and_write_rsa_keypair(self.key_path2)
    self.key = prompt_import_rsa_key_from_file(self.key_path)
    self.key2 = prompt_import_rsa_key_from_file(self.key_path2)

    self.step_name = "test-step"
    self.link_name = "{}.{:.8}.link".format(self.step_name, self.key["keyid"])
    self.link_name_unfinished = UNFINISHED_FILENAME_FORMAT.format(
        step_name=self.step_name, keyid=self.key["keyid"])

    self.test_product = "test_product"
    open(self.test_product, "w").close()

  @classmethod
  def tearDownClass(self):
    """Change back to initial working dir and remove temp test directory. """
    os.chdir(self.working_dir)
    shutil.rmtree(self.test_dir)

  def test_create_metadata_with_expected_product(self):
    """Test record stop records expected product. """
    in_toto_record_start(self.step_name, [], self.key)
    in_toto_record_stop(self.step_name, [self.test_product], self.key)
    link = Metablock.load(self.link_name)
    self.assertEquals(link.signed.products.keys(), [self.test_product])
    os.remove(self.link_name)

  def test_create_metadata_with_expected_cwd(self):
    """Test record start/stop run, verify cwd. """
    in_toto_record_start(self.step_name, [], self.key)
    in_toto_record_stop(self.step_name, [self.test_product], self.key)
    link = Metablock.load(self.link_name)
    self.assertEquals(link.signed.environment["workdir"], os.getcwd())
    os.remove(self.link_name)

  def test_create_metadata_verify_signature(self):
    """Test record start creates metadata with expected signature. """
    in_toto_record_start(self.step_name, [], self.key)
    in_toto_record_stop(self.step_name, [], self.key)
    link = Metablock.load(self.link_name)
    link.verify_signatures({self.key["keyid"] : self.key})
    os.remove(self.link_name)

  def test_replace_unfinished_metadata(self):
    """Test record stop removes unfinished file and creates link file. """
    in_toto_record_start(self.step_name, [], self.key)
    in_toto_record_stop(self.step_name, [], self.key)
    with self.assertRaises(IOError):
      open(self.link_name_unfinished, "r")
    open(self.link_name, "r")
    os.remove(self.link_name)

  def test_missing_unfinished_file(self):
    """Test record stop exits on missing unfinished file, no link recorded. """
    with self.assertRaises(IOError):
      in_toto_record_stop(self.step_name, [], self.key)
    with self.assertRaises(IOError):
      open(self.link_name, "r")

  def test_wrong_signature_in_unfinished_metadata(self):
    """Test record stop exits on wrong signature, no link recorded. """
    in_toto_record_start(self.step_name, [], self.key)
    link_name = UNFINISHED_FILENAME_FORMAT.format(
        step_name=self.step_name, keyid=self.key["keyid"])
    changed_link_name = UNFINISHED_FILENAME_FORMAT.format(
        step_name=self.step_name, keyid=self.key2["keyid"])
    os.rename(link_name, changed_link_name)
    with self.assertRaises(SignatureVerificationError):
      in_toto_record_stop(self.step_name, [], self.key2)
    with self.assertRaises(IOError):
      open(self.link_name, "r")
    os.rename(changed_link_name, link_name)
    os.remove(self.link_name_unfinished)

if __name__ == "__main__":
  unittest.main()
