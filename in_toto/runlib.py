"""
<Program Name>
  runlib.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  June 27, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides a wrapper for any command of the software supply chain.

  The wrapper performs the following tasks which are implemented in this
  library.

    - Record state of material (files the command is executed on)
    - Execute command
      - Capture stdout/stderr/return value of the executed command
    - Record state of product (files after the command was executed)
    - Return Metablock containing a Link object which can be can be signed
      and stored to disk
"""
import sys
import os
import tempfile
import fnmatch

import in_toto.settings
import in_toto.exceptions
from in_toto import log
from in_toto.models.link import (UNFINISHED_FILENAME_FORMAT, FILENAME_FORMAT,
    FILENAME_FORMAT_SHORT)

import securesystemslib.formats
import securesystemslib.hash
import securesystemslib.exceptions

from in_toto.models.metadata import Metablock

# POSIX users (Linux, BSD, etc.) are strongly encouraged to
# install and use the much more recent subprocess32
if os.name == 'posix' and sys.version_info[0] < 3:
  try:
    import subprocess32 as subprocess
  except ImportError:
    log.warn("POSIX users (Linux, BSD, etc.) are strongly encouraged to"
        " install and use the much more recent subprocess32")
    import subprocess
else:
  import subprocess


def _hash_artifact(filepath, hash_algorithms=['sha256']):
  """Internal helper that takes a filename and hashes the respective file's
  contents using the passed hash_algorithms and returns a hashdict conformant
  with securesystemslib.formats.HASHDICT_SCHEMA. """
  securesystemslib.formats.HASHALGORITHMS_SCHEMA.check_match(hash_algorithms)
  hash_dict = {}

  for algorithm in hash_algorithms:
    digest_object = securesystemslib.hash.digest_filename(filepath, algorithm)
    hash_dict.update({algorithm: digest_object.hexdigest()})

  securesystemslib.formats.HASHDICT_SCHEMA.check_match(hash_dict)

  return hash_dict


def _apply_exclude_patterns(names, exclude_patterns):
  """Exclude matched patterns from passed names. """

  for exclude_pattern in exclude_patterns:
    excludes = fnmatch.filter(names, exclude_pattern)
    names = list(set(names) - set(excludes))
  return names


def record_artifacts_as_dict(artifacts):
  """
  <Purpose>
    Hashes each file in the passed path list. If the path list contains
    paths to directories the directory tree(s) are traversed.

    The files a link command is executed on are called materials.
    The files that result form a link command execution are called
    products.

    Paths are normalized for matching and storing by left stripping "./"

    Excludes files that are matched by the file patterns specified in
    ARTIFACT_EXCLUDE_PATTERNS setting.

    EXCLUDES:
      - Uses Python fnmatch
            *       matches everything
            ?       matches any single character
            [seq]   matches any character in seq
            [!seq]  matches any character not in seq

      - Patterns are checked for match against the full path relative to each
        path passed in the artifacts list

      - If a directory is excluded, all its files and subdirectories are also
        excluded

      - How it differs from .gitignore
            - No need to escape #
            - No ignoring of trailing spaces
            - No general negation with exclamation mark !
            - No special treatment of slash /
            - No special treatment of consecutive asterisks **

      - Exclude patterns are likely to become command line arguments or part of
        a config file.

  <Arguments>
    artifacts:
            A list of file or directory paths used as materials or products for
            the link command.

  <Exceptions>
    in_toto.exceptions.SettingsError
        if ARTIFACT_BASE_PATH or ARTIFACT_EXCLUDE_PATTERNS can't be used

  <Side Effects>
    Calls functions to generate cryptographic hashes.

  <Returns>
    A dictionary with file paths as keys and the files' hashes as values.
  """
  artifacts_dict = {}

  if not artifacts:
    return artifacts_dict

  # Temporarily change into base path dir if set
  if in_toto.settings.ARTIFACT_BASE_PATH:
    original_cwd = os.getcwd()
    try:
      os.chdir(in_toto.settings.ARTIFACT_BASE_PATH)
    except Exception as e:
      raise in_toto.exceptions.SettingsError(
          "Review your ARTIFACT_BASE_PATH setting '{}' - {}".format(
          in_toto.settings.ARTIFACT_BASE_PATH, e))

  # Normalize passed paths
  norm_artifacts = []
  for path in artifacts:
    norm_artifacts.append(os.path.normpath(path))

  # If ARTIFACT_EXCLUDE_PATTERNS is set it must be a list of strings or an empty list
  # TODO: Change NAMES_SCHEMA to something more semantically accurate
  if (in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS and not
      securesystemslib.formats.NAMES_SCHEMA.matches(
      in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS)):
    raise in_toto.exceptions.SettingsError(
        "Review your ARTIFACT_EXCLUDE_PATTERNS setting '{}'".format(
        in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS))

  # Iterate over remaining normalized artifact paths after
  # having applied exclusion patterns
  for artifact in _apply_exclude_patterns(norm_artifacts,
      in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS):

    if not os.path.exists(artifact):
      log.warn("path: {} does not exist, skipping..".format(artifact))
      continue

    if os.path.isfile(artifact):
      # Path was already normalized above
      artifacts_dict[artifact] = _hash_artifact(artifact)

    elif os.path.isdir(artifact):
      for root, dirs, files in os.walk(artifact):

        # Create a list of normalized dirpaths
        dirpaths = []
        for dirname in dirs:
          norm_dirpath = os.path.normpath(os.path.join(root, dirname))
          dirpaths.append(norm_dirpath)

        # Apply exlcude patterns on normalized dirpaths
        dirpaths = _apply_exclude_patterns(dirpaths,
            in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS)

        # Reset and refill dirs with remaining names after exclusion
        # Modify (not reassign) dirnames to only recurse into remaining dirs
        dirs[:] = []
        for dirpath in dirpaths:
          # Dirs only contain the basename and not the full path
          name = os.path.basename(dirpath)
          dirs.append(name)

        # Create a list of normalized filepaths
        filepaths = []
        for filename in files:
          norm_filepath = os.path.normpath(os.path.join(root, filename))

          # `os.walk` could also list dead symlinks, which would
          # result in an error later when trying to read the file
          if os.path.isfile(norm_filepath):
            filepaths.append(norm_filepath)
          else:
            log.warn("File '{}' appears to be a broken symlink. Skipping..."
                .format(norm_filepath))

        # Apply exclude patterns on normalized filepaths and
        # store each remaining normalized filepath with it's files hash to
        # the resulting artifact dict
        for filepath in _apply_exclude_patterns(filepaths,
            in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS):
          artifacts_dict[filepath] = _hash_artifact(filepath)

  # Change back to where original current working dir
  if in_toto.settings.ARTIFACT_BASE_PATH:
    os.chdir(original_cwd)

  return artifacts_dict

def execute_link(link_cmd_args, record_streams):
  """
  <Purpose>
    Executes the passed command plus arguments in a subprocess and returns
    the return value of the executed command. If the specified standard output
    and standard error of the command are recorded and also returned to the
    caller.

  <Arguments>
    link_cmd_args:
            A list where the first element is a command and the remaining
            elements are arguments passed to that command.
    record_streams:
            A bool that specifies whether to redirect standard output and
            and standard error to a temporary file which is returned to the
            caller (True) or not (False).

  <Exceptions>
    TBA (see https://github.com/in-toto/in-toto/issues/6)

  <Side Effects>
    Executes passed command in a subprocess and redirects stdout and stderr
    if specified.

  <Returns>
    - A dictionary containg standard output and standard error of the
      executed command, called by-products.
      Note: If record_streams is False, the dict values are empty strings.
    - The return value of the executed command.
  """
  # XXX: The first approach only redirects the stdout/stderr to a tempfile
  # but we actually want to duplicate it, ideas
  #  - Using a pipe won't work because processes like vi will complain
  #  - Wrapping stdout/sterr in Python does not work because the suprocess
  #    will only take the fd and then uses it natively
  #  - Reading from /dev/stdout|stderr, /dev/tty is *NIX specific

  # Until we come up with a proper solution we use a flag and let the user
  # decide if s/he wants to see or store stdout/stderr
  # btw: we ignore them in the layout anyway

  if record_streams:
    # XXX: Use SpooledTemporaryFile if we expect very large outputs
    stdout_file = tempfile.TemporaryFile()
    stderr_file = tempfile.TemporaryFile()

    return_value = subprocess.call(link_cmd_args,
        stdout=stdout_file, stderr=stderr_file)

    stdout_file.seek(0)
    stderr_file.seek(0)

    stdout_str = stdout_file.read()
    stderr_str = stderr_file.read()

  else:
      return_value = subprocess.call(link_cmd_args)
      stdout_str = stderr_str = ""

  return {
      "stdout": stdout_str,
      "stderr": stderr_str,
      "return-value": return_value
    }


def in_toto_mock(name, link_cmd_args):
  """
  <Purpose>
    in_toto_run with defaults
     - Records materials and products in current directory
     - Does not sign resulting link file
     - Stores resulting link file under "<name>.link"

  <Arguments>
    name:
            A unique name to relate mock link metadata with a step or
            inspection defined in the layout.
    link_cmd_args:
            A list where the first element is a command and the remaining
            elements are arguments passed to that command.

  <Exceptions>
    None.

  <Side Effects>
    Writes newly created link metadata file to disk using the filename scheme
    from link.FILENAME_FORMAT_SHORT

  <Returns>
    Newly created Metablock object containing a Link object

  """
  link = in_toto_run(name, ["."], ["."], link_cmd_args, key=False,
      record_streams=True)

  link_metadata = Metablock(signed=link)

  filename = FILENAME_FORMAT_SHORT.format(step_name=name)
  log.info("Storing unsigned link metadata to '{}.link'...".format(filename))
  link_metadata.dump(filename)
  return link_metadata


def in_toto_run(name, material_list, product_list,
    link_cmd_args, key=False, record_streams=False):
  """
  <Purpose>
    Calls function to run command passed as link_cmd_args argument, storing
    its materials, by-products and return value, and products into a link
    metadata file. The link metadata file is signed with the passed key and
    stored to disk.

  <Arguments>
    name:
            A unique name to relate link metadata with a step or inspection
            defined in the layout.
    material_list:
            List of file or directory paths that should be recorded as
            materials.
    product_list:
            List of file or directory paths that should be recorded as
            products.
    link_cmd_args:
            A list where the first element is a command and the remaining
            elements are arguments passed to that command.
    key: (optional)
            Private key to sign link metadata.
            Format is securesystemslib.formats.KEY_SCHEMA
    record_streams: (optional)
            A bool that specifies whether to redirect standard output and
            and standard error to a temporary file which is returned to the
            caller (True) or not (False).

  <Exceptions>
    None.

  <Side Effects>
    Writes newly created link metadata file to disk using the filename scheme
    from link.FILENAME_FORMAT

  <Returns>
    Newly created Metablock object containing a Link object

  """

  log.info("Running '{}'...".format(name))

  # If a key is passed, it has to match the format
  if key:
    securesystemslib.formats.KEY_SCHEMA.check_match(key)
    #FIXME: Add private key format check to securesystemslib formats
    if not key["keyval"].get("private"):
      raise securesystemslib.exceptions.FormatError(
          "Signing key needs to be a private key.")

  if material_list:
    log.info("Recording materials '{}'...".format(", ".join(material_list)))
  materials_dict = record_artifacts_as_dict(material_list)

  if link_cmd_args:
    log.info("Running command '{}'...".format(" ".join(link_cmd_args)))
    byproducts = execute_link(link_cmd_args, record_streams)
  else:
    byproducts = {}

  if product_list:
    log.info("Recording products '{}'...".format(", ".join(product_list)))
  products_dict = record_artifacts_as_dict(product_list)

  log.info("Creating link metadata...")
  link = in_toto.models.link.Link(name=name,
      materials=materials_dict, products=products_dict, command=link_cmd_args,
      byproducts=byproducts, environment={"workdir": os.getcwd()})

  link_metadata = Metablock(signed=link)

  if key:
    log.info("Signing link metadata with key '{:.8}...'...".format(key["keyid"]))
    link_metadata.sign(key)

    filename = FILENAME_FORMAT.format(step_name=name, keyid=key["keyid"])
    log.info("Storing link metadata to '{}'...".format(filename))
    link_metadata.dump(filename)

  return link_metadata


def in_toto_record_start(step_name, key, material_list):
  """
  <Purpose>
    Starts creating link metadata for a multi-part in-toto step. I.e.
    records passed materials, creates link meta data object from it, signs it
    with passed key and stores it to disk with UNFINISHED_FILENAME_FORMAT.

  <Arguments>
    step_name:
            A unique name to relate link metadata with a step defined in the
            layout.
    key:
            Private key to sign link metadata.
            Format is securesystemslib.formats.KEY_SCHEMA
    material_list:
            List of file or directory paths that should be recorded as
            materials.

  <Exceptions>
    None.

  <Side Effects>
    Writes newly created link metadata file to disk using the filename scheme
    from link.UNFINISHED_FILENAME_FORMAT

  <Returns>
    None.

  """

  unfinished_fn = UNFINISHED_FILENAME_FORMAT.format(step_name=step_name, keyid=key["keyid"])
  log.info("Start recording '{}'...".format(step_name))

  if material_list:
    log.info("Recording materials '{}'...".format(", ".join(material_list)))
  materials_dict = record_artifacts_as_dict(material_list)

  log.info("Creating preliminary link metadata...")
  link = in_toto.models.link.Link(name=step_name,
          materials=materials_dict, products={}, command=[], byproducts={},
          environment={"workdir": os.getcwd()})

  link_metadata = Metablock(signed=link)

  log.info("Signing link metadata with key '{:.8}...'...".format(key["keyid"]))
  link_metadata.sign(key)

  log.info("Storing preliminary link metadata to '{}'...".format(unfinished_fn))
  link_metadata.dump(unfinished_fn)


def in_toto_record_stop(step_name, key, product_list):
  """
  <Purpose>
    Finishes creating link metadata for a multi-part in-toto step.
    Loads signing key and unfinished link metadata file from disk, verifies
    that the file was signed with the key, records products, updates unfinished
    Link object (products and signature), removes unfinished link file from and
    stores new link file to disk.

  <Arguments>
    step_name:
            A unique name to relate link metadata with a step defined in the
            layout.
    key:
            Private key to sign link metadata.
            Format is securesystemslib.formats.KEY_SCHEMA
    product_list:
            List of file or directory paths that should be recorded as products.

  <Exceptions>
    None.

  <Side Effects>
    Writes newly created link metadata file to disk using the filename scheme
    from link.FILENAME_FORMAT
    Removes unfinished link file link.UNFINISHED_FILENAME_FORMAT from disk

  <Returns>
    None.

  """
  fn = FILENAME_FORMAT.format(step_name=step_name, keyid=key["keyid"])
  unfinished_fn = UNFINISHED_FILENAME_FORMAT.format(step_name=step_name, keyid=key["keyid"])
  log.info("Stop recording '{}'...".format(step_name))

  # Expects an a file with name UNFINISHED_FILENAME_FORMAT in the current dir
  log.info("Loading preliminary link metadata '{}'...".format(unfinished_fn))
  link_metadata = Metablock.load(unfinished_fn)

  # The file must have been signed by the same key
  log.info("Verifying preliminary link signature...")
  keydict = {key["keyid"] : key}
  link_metadata.verify_signatures(keydict)

  if product_list:
    log.info("Recording products '{}'...".format(", ".join(product_list)))
  link_metadata.signed.products = record_artifacts_as_dict(product_list)

  log.info("Updating signature with key '{:.8}...'...".format(key["keyid"]))
  link_metadata.signatures = []
  link_metadata.sign(key)

  log.info("Storing link metadata to '{}'...".format(fn))
  link_metadata.dump(fn)

  log.info("Removing unfinished link metadata '{}'...".format(unfinished_fn))
  os.remove(unfinished_fn)
