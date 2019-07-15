#!/usr/bin/env python
#coding=utf-8

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
    in_toto_record_stop, record_artifacts_as_dict, _apply_exclude_patterns,
    _hash_artifact)
from in_toto.util import (generate_and_write_rsa_keypair,
    prompt_import_rsa_key_from_file)
from in_toto.models.link import UNFINISHED_FILENAME_FORMAT, FILENAME_FORMAT

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

    # Create files on 3 levels
    os.mkdir("subdir")
    os.mkdir("subdir/subsubdir")

    self.full_file_path_list = ["foo", "bar", "subdir/foosub1",
        "subdir/foosub2", "subdir/subsubdir/foosubsub"]

    for path in self.full_file_path_list:
      with open(path, "w") as fp:
        fp.write(path)


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
    for base_path in ["path/does/not/exist", 12345, True]:
      in_toto.settings.ARTIFACT_BASE_PATH = base_path
      with self.assertRaises(ValueError):
        record_artifacts_as_dict(["."])
      in_toto.settings.ARTIFACT_BASE_PATH = None

      with self.assertRaises(ValueError):
        record_artifacts_as_dict(["."], base_path=base_path)


  def test_base_path_is_child_dir(self):
    """Test path of recorded artifacts and cd back with child as base."""
    base_path = "subdir"
    expected_artifacts = sorted(["foosub1", "foosub2", "subsubdir/foosubsub"])

    in_toto.settings.ARTIFACT_BASE_PATH = base_path
    artifacts_dict = record_artifacts_as_dict(["."])
    self.assertListEqual(sorted(list(artifacts_dict.keys())),
        expected_artifacts)
    in_toto.settings.ARTIFACT_BASE_PATH = None

    artifacts_dict = record_artifacts_as_dict(["."], base_path=base_path)
    self.assertListEqual(sorted(list(artifacts_dict.keys())),
        expected_artifacts)


  def test_base_path_is_parent_dir(self):
    """Test path of recorded artifacts and cd back with parent as base. """
    base_path = ".."
    expected_artifacts = sorted(["foosub1", "foosub2", "subsubdir/foosubsub"])
    os.chdir("subdir/subsubdir")

    in_toto.settings.ARTIFACT_BASE_PATH = base_path
    artifacts_dict = record_artifacts_as_dict(["."])
    self.assertListEqual(sorted(list(artifacts_dict.keys())),
        expected_artifacts)
    in_toto.settings.ARTIFACT_BASE_PATH = None

    artifacts_dict = record_artifacts_as_dict(["."], base_path=base_path)
    self.assertListEqual(sorted(list(artifacts_dict.keys())),
        expected_artifacts)

    os.chdir(self.test_dir)


  def test_lstrip_paths_valid_prefix_directory(self):
    lstrip_paths = ["subdir/subsubdir/"]
    expected_artifacts = sorted(["bar", "foo", "subdir/foosub1",
        "subdir/foosub2", "foosubsub"])
    artifacts_dict = record_artifacts_as_dict(["."],
        lstrip_paths=lstrip_paths)
    self.assertListEqual(sorted(list(artifacts_dict.keys())),
        expected_artifacts)


  def test_lstrip_paths_substring_prefix_directory(self):
    lstrip_paths = ["subdir/subsubdir/", "subdir/"]
    with self.assertRaises(in_toto.exceptions.PrefixError):
      record_artifacts_as_dict(["."], lstrip_paths=lstrip_paths)


  def test_lstrip_paths_non_unique_key(self):
    os.mkdir("subdir_new")
    path = "subdir_new/foosub1"
    shutil.copy("subdir/foosub1", path)
    lstrip_paths = ["subdir/", "subdir_new/"]
    with self.assertRaises(in_toto.exceptions.PrefixError):
      record_artifacts_as_dict(["."], lstrip_paths=lstrip_paths)
    os.remove(path)
    os.rmdir("subdir_new")


  def test_lstrip_paths_invalid_prefix_directory(self):
    lstrip_paths = ["not/a/directory/"]
    expected_artifacts = sorted(["bar", "foo", "subdir/foosub1",
                                 "subdir/foosub2", "subdir/subsubdir/foosubsub"])
    artifacts_dict = record_artifacts_as_dict(["."],
        lstrip_paths=lstrip_paths)
    self.assertListEqual(sorted(list(artifacts_dict.keys())),
                         expected_artifacts)


  def test_lstrip_paths_valid_prefix_file(self):
    lstrip_paths = ["subdir/subsubdir/"]
    expected_artifacts = sorted(["foosubsub"])
    artifacts_dict = record_artifacts_as_dict(["./subdir/subsubdir/foosubsub"],
        lstrip_paths=lstrip_paths)
    self.assertListEqual(sorted(list(artifacts_dict.keys())),
        expected_artifacts)


  def test_lstrip_paths_non_unique_key_file(self):
    os.mkdir("subdir/subsubdir_new")
    path = "subdir/subsubdir_new/foosubsub"
    shutil.copy("subdir/subsubdir/foosubsub", path)
    lstrip_paths = ["subdir/subsubdir/", "subdir/subsubdir_new/"]
    with self.assertRaises(in_toto.exceptions.PrefixError):
      record_artifacts_as_dict(["subdir/subsubdir/foosubsub",
          "subdir/subsubdir_new/foosubsub"], lstrip_paths=lstrip_paths)
    os.remove(path)
    os.rmdir("subdir/subsubdir_new")


  def test_lstrip_paths_valid_unicode_prefix_file(self):
    # Try to create a file with unicode character
    try:
      os.mkdir("ಠ")
      path = "ಠ/foo"
      shutil.copy("foo", path)

      # Attempt to left strip the path now that the file has been created
      lstrip_paths = ["ಠ/"]
      expected_artifacts = sorted(["foo"])
      artifacts_dict = record_artifacts_as_dict(["./ಠ/"],
          lstrip_paths=lstrip_paths)
      self.assertListEqual(sorted(list(artifacts_dict.keys())),
          expected_artifacts)
      os.remove(path)
      os.rmdir("ಠ")
    except OSError:
      # OS doesn't support unicode explicit files
      pass


  def test_empty_artifacts_list_record_nothing(self):
    """Empty list passed. Return empty dict. """
    self.assertDictEqual(record_artifacts_as_dict([]), {})

  def test_not_existing_artifacts_in_list_record_nothing(self):
    """List with not existing artifact passed. Return empty dict. """
    self.assertDictEqual(record_artifacts_as_dict(["baz"]), {})

  def test_record_dot_check_files_hash_dict_schema(self):
    """Traverse dir and subdirs. Record three files. """
    artifacts_dict = record_artifacts_as_dict(["."])

    for val in list(artifacts_dict.values()):
      securesystemslib.formats.HASHDICT_SCHEMA.check_match(val)

    self.assertListEqual(sorted(list(artifacts_dict.keys())),
      sorted(self.full_file_path_list))


  @unittest.skipIf("symlink" not in os.__dict__, "symlink is not supported in this platform")
  def test_record_symlinked_files(self):
    """Symlinked files are always recorded. """
    # Symlinked **files** are always recorded ...
    link_pairs = [
      ("foo", "foo_link"),
      ("subdir/foosub1", "subdir/foosub2_link"),
      ("subdir/subsubdir/foosubsub", "subdir/subsubdir/foosubsub_link")
    ]

    # Create links
    for pair in link_pairs:
      # We only use the basename of the file (source) as it is on the same
      # level as the link (target)
      os.symlink(os.path.basename(pair[0]), pair[1])

    # Record files and linked files
    # follow_symlink_dirs does not make a difference as it only concerns linked dirs
    for follow_symlink_dirs in [True, False]:
      artifacts_dict = record_artifacts_as_dict(["."],
          follow_symlink_dirs=follow_symlink_dirs)

      # Test that everything was recorded ...
      self.assertListEqual(sorted(list(artifacts_dict.keys())),
          sorted(self.full_file_path_list + [pair[1] for pair in link_pairs]))

      # ... and the hashes of each link/file pair match
      for pair in link_pairs:
        self.assertDictEqual(artifacts_dict[pair[0]], artifacts_dict[pair[1]])

    for pair in link_pairs:
      os.unlink(pair[1])


  @unittest.skipIf("symlink" not in os.__dict__, "symlink is not supported in this platform")
  def test_record_without_dead_symlinks(self):
    """Dead symlinks are never recorded. """

    # Dead symlinks are never recorded ...
    links = [
      "foo_link",
      "subdir/foosub2_link",
      "subdir/subsubdir/foosubsub_link"
    ]

    # Create dead links
    for link in links:
      os.symlink("does/not/exist", link)

    # Record files without dead links
    # follow_symlink_dirs does not make a difference as it only concerns linked dirs
    for follow_symlink_dirs in [True, False]:
      artifacts_dict = record_artifacts_as_dict(["."],
          follow_symlink_dirs=follow_symlink_dirs)

      # Test only the files were recorded ...
      self.assertListEqual(sorted(list(artifacts_dict.keys())),
          sorted(self.full_file_path_list))

    for link in links:
      os.unlink(link)


  @unittest.skipIf("symlink" not in os.__dict__, "symlink is not supported in this platform")
  def test_record_follow_symlinked_directories(self):
    """Record files in symlinked dirs if follow_symlink_dirs is True. """

    # Link to subdir
    os.symlink("subdir", "subdir_link")

    link_pairs = [
      ("subdir/foosub1", "subdir_link/foosub1"),
      ("subdir/foosub2", "subdir_link/foosub2"),
      ("subdir/subsubdir/foosubsub", "subdir_link/subsubdir/foosubsub"),
    ]

    # Record with follow_symlink_dirs TRUE
    artifacts_dict = record_artifacts_as_dict(["."], follow_symlink_dirs=True)
    # Test that all files were recorded including files in linked subdir ...
    self.assertListEqual(sorted(list(artifacts_dict.keys())),
        sorted(self.full_file_path_list + [pair[1] for pair in link_pairs]))

    # ... and the hashes of each link/file pair match
    for pair in link_pairs:
      self.assertDictEqual(artifacts_dict[pair[0]], artifacts_dict[pair[1]])


    # Record with follow_symlink_dirs FALSE (default)
    artifacts_dict = record_artifacts_as_dict(["."])
    self.assertListEqual(sorted(list(artifacts_dict.keys())),
        sorted(self.full_file_path_list))

    os.unlink("subdir_link")


  def test_record_files_and_subdirs(self):
    """Explicitly record files and subdirs. """
    artifacts_dict = record_artifacts_as_dict(["foo", "subdir"])

    for val in list(artifacts_dict.values()):
      securesystemslib.formats.HASHDICT_SCHEMA.check_match(val)

    self.assertListEqual(sorted(list(artifacts_dict.keys())),
      sorted(["foo", "subdir/foosub1", "subdir/foosub2",
          "subdir/subsubdir/foosubsub"]))


  def test_exclude_patterns(self):
    """Test excluding artifacts using passed pattern or setting. """
    excludes_and_results = [
      # Exclude files containing 'foo' everywhere
      (["*foo*"], ["bar"]),
      # Exclude subdirectory and all its contents
      (["subdir"], ["bar", "foo"]),
      # Exclude files 'subdir/foosub1' and 'subdir/foosub2'
      (["*foosub?"], ["bar", "foo", "subdir/subsubdir/foosubsub"]),
      # Exclude subsubdirectory and its contents
      (["*subsubdir"], ["foo", "bar", "subdir/foosub1", "subdir/foosub2"])
      ]

    for exclude_patterns, expected_results in excludes_and_results:
      # Exclude via setting
      in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS = exclude_patterns
      artifacts1 = record_artifacts_as_dict(["."])

      # Exclude via argument
      in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS = None
      artifacts2 = record_artifacts_as_dict(["."],
          exclude_patterns=exclude_patterns)

      self.assertTrue(sorted(list(artifacts1)) == sorted(list(artifacts2))
          == sorted(expected_results))


  def test_bad_artifact_exclude_patterns_setting(self):
    """Raise exception with bogus artifact exclude patterns settings. """
    for setting in ["not a list of settings", 12345, True]:
      in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS = setting
      with self.assertRaises(securesystemslib.exceptions.FormatError):
        record_artifacts_as_dict(["."])

  def test_hash_artifact_passing_algorithm(self):
    """Test _hash_artifact passing hash algorithm. """
    os.chdir(self.test_dir)
    self.assertTrue("sha256" in list(_hash_artifact("foo", ["sha256"]).keys()))


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
        ["python", "--version"], True, self.key)
    link.verify_signature(self.key)

  def test_in_toto_run_no_signature(self):
    """Successfully run, verify empty signature field. """
    link = in_toto_run(self.step_name, None, None, ["python", "--version"])
    self.assertFalse(len(link.signatures))

  def test_in_toto_run_with_byproduct(self):
    """Successfully run, verify recorded byproduct. """
    link = in_toto_run(self.step_name, None, None, ["python", "--version"],
        record_streams=True)

    # this or clause may seem weird, but given that python 2 prints its version
    # to stderr while python3 prints it to stdout we check on both (or add a
    # more verbose if clause)
    stderr_contents = link.signed.byproducts.get("stderr")
    stdout_contents = link.signed.byproducts.get("stdout")
    self.assertTrue("Python" in stderr_contents or "Python" in stdout_contents,
        msg="\nSTDERR:\n{}\nSTDOUT:\n{}".format(stderr_contents, stdout_contents))

  def test_in_toto_run_without_byproduct(self):
    """Successfully run, verify byproduct is not recorded. """
    link = in_toto_run(self.step_name, None, None, ["python", "--version"],
        record_streams=False)
    self.assertFalse(len(link.signed.byproducts.get("stdout")))

  def test_in_toto_run_compare_dumped_with_returned_link(self):
    """Successfully run, compare dumped link is equal to returned link. """
    link = in_toto_run(self.step_name, [self.test_artifact],
        [self.test_artifact], ["python", "--version"], True, self.key)
    link_dump = Metablock.load(
        FILENAME_FORMAT.format(step_name=self.step_name, keyid=self.key["keyid"]))
    self.assertEqual(repr(link), repr(link_dump))

  def test_in_toto_run_verify_recorded_artifacts(self):
    """Successfully run, verify properly recorded artifacts. """
    link = in_toto_run(self.step_name, [self.test_artifact],
        [self.test_artifact], ["python", "--version"])
    self.assertEqual(list(link.signed.materials.keys()),
        list(link.signed.products.keys()), [self.test_artifact])

  def test_in_toto_run_verify_workdir(self):
    """Successfully run, verify cwd. """
    link = in_toto_run(self.step_name, [], [], ["python", "--version"],
        record_environment=True)
    self.assertEqual(link.signed.environment["workdir"],
        os.getcwd().replace("\\", "/"))

  def test_normalize_line_endings(self):
    """Test cross-platform line ending normalization. """
    paths = []
    try:
      # Create three artifacts with same content but different line endings
      for line_ending in [b"\n", b"\r", b"\r\n"]:
        fd, path = tempfile.mkstemp()
        paths.append(path)
        os.write(fd, b"hello" + line_ending + b"toto")
        os.close(fd)

      # Call in_toto_run and record artifacts as materials and products
      # with line ending normalization on
      link = in_toto_run(self.step_name, paths, paths, ["python", "--version"],
          normalize_line_endings=True).signed

      # Check that all three hashes in materials and products are equal
      for artifact_dict in [link.materials, link.products]:
        hash_dicts = list(artifact_dict.values())
        self.assertTrue(hash_dicts[1:] == hash_dicts[:-1])

    # Clean up
    finally:
      for path in paths:
        os.remove(path)


  def test_in_toto_bad_signing_key_format(self):
    """Fail run, passed key is not properly formatted. """
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      in_toto_run(self.step_name, None, None,
          ["python", "--version"], True, "this-is-not-a-key")

  def test_in_toto_wrong_key(self):
    """Fail run, passed key is a public key. """
    with self.assertRaises(securesystemslib.exceptions.FormatError):
      in_toto_run(self.step_name, None, None,
          ["python", "--version"], True, self.key_pub)


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

    self.test_material = "test_material"
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
    self.assertEqual(list(link.signed.materials.keys()), [self.test_material])
    os.remove(self.link_name_unfinished)

  def test_create_unfininished_metadata_verify_signature(self):
    """Test record start creates metadata with expected signature. """
    in_toto_record_start(
        self.step_name, [self.test_material], self.key)
    link = Metablock.load(self.link_name_unfinished)
    link.verify_signature(self.key)
    os.remove(self.link_name_unfinished)

  def test_no_key_arguments(self):
    """Test record start without passing one required key argument. """
    with self.assertRaises(ValueError):
      in_toto_record_start(
          self.step_name, [], signing_key=None, gpg_keyid=None,
          gpg_use_default=False)

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
    self.assertEqual(list(link.signed.products.keys()), [self.test_product])
    os.remove(self.link_name)

  def test_create_metadata_with_expected_cwd(self):
    """Test record start/stop run, verify cwd. """
    in_toto_record_start(self.step_name, [], self.key, record_environment=True)
    in_toto_record_stop(self.step_name, [self.test_product], self.key)
    link = Metablock.load(self.link_name)
    self.assertEqual(link.signed.environment["workdir"],
        os.getcwd().replace('\\', '/'))
    os.remove(self.link_name)

  def test_create_metadata_verify_signature(self):
    """Test record start creates metadata with expected signature. """
    in_toto_record_start(self.step_name, [], self.key)
    in_toto_record_stop(self.step_name, [], self.key)
    link = Metablock.load(self.link_name)
    link.verify_signature(self.key)
    os.remove(self.link_name)

  def test_replace_unfinished_metadata(self):
    """Test record stop removes unfinished file and creates link file. """
    in_toto_record_start(self.step_name, [], self.key)
    in_toto_record_stop(self.step_name, [], self.key)
    with self.assertRaises(IOError):
      open(self.link_name_unfinished, "r")
    self.assertTrue(os.path.isfile(self.link_name))
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

  def test_no_key_arguments(self):
    """Test record stop without passing one required key argument. """
    with self.assertRaises(ValueError):
      in_toto_record_stop(
          self.step_name, [], signing_key=None, gpg_keyid=None,
          gpg_use_default=False)

  def test_normalize_line_endings(self):
    """Test cross-platform line ending normalization. """
    paths = []
    try:
      # Create three artifacts with same content but different line endings
      for line_ending in [b"\n", b"\r", b"\r\n"]:
        fd, path = tempfile.mkstemp()
        paths.append(path)
        os.write(fd, b"hello" + line_ending + b"toto")
        os.close(fd)

      # Call in_toto_record start and stop and record artifacts as
      # materials and products with line ending normalization on
      in_toto_record_start(self.step_name, paths, self.key,
          normalize_line_endings=True)
      in_toto_record_stop(self.step_name, paths, self.key,
          normalize_line_endings=True)
      link = Metablock.load(self.link_name).signed

      # Check that all three hashes in materials and products are equal
      for artifact_dict in [link.materials, link.products]:
        hash_dicts = list(artifact_dict.values())
        self.assertTrue(hash_dicts[1:] == hash_dicts[:-1])

    # Clean up
    finally:
      for path in paths:
        os.remove(path)


if __name__ == "__main__":
  unittest.main()
