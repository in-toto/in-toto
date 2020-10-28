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
import six
import glob
import logging
import os
import itertools

from pathspec import PathSpec

import in_toto.settings
import in_toto.exceptions

from in_toto.models.link import (UNFINISHED_FILENAME_FORMAT, FILENAME_FORMAT,
    FILENAME_FORMAT_SHORT, UNFINISHED_FILENAME_FORMAT_GLOB)

import securesystemslib.formats
import securesystemslib.hash
import securesystemslib.exceptions
import securesystemslib.process
import securesystemslib.gpg

from in_toto.models.metadata import Metablock


# Inherits from in_toto base logger (c.f. in_toto.log)
LOG = logging.getLogger(__name__)





def _hash_artifact(filepath, hash_algorithms=None,
      normalize_line_endings=False):
  """Internal helper that takes a filename and hashes the respective file's
  contents using the passed hash_algorithms and returns a hashdict conformant
  with securesystemslib.formats.HASHDICT_SCHEMA. """
  if not hash_algorithms:
    hash_algorithms = ['sha256']

  securesystemslib.formats.HASHALGORITHMS_SCHEMA.check_match(hash_algorithms)
  hash_dict = {}

  for algorithm in hash_algorithms:
    digest_object = securesystemslib.hash.digest_filename(filepath, algorithm,
        normalize_line_endings=normalize_line_endings)
    hash_dict.update({algorithm: digest_object.hexdigest()})

  securesystemslib.formats.HASHDICT_SCHEMA.check_match(hash_dict)

  return hash_dict


def _apply_exclude_patterns(names, exclude_filter):
  """Exclude matched patterns from passed names."""
  included = set(names)

  # Assume old way for easier testing
  if hasattr(exclude_filter, '__iter__'):
    exclude_filter = PathSpec.from_lines('gitwildmatch', exclude_filter)

  for excluded in exclude_filter.match_files(names):
    included.discard(excluded)

  return sorted(included)


def _apply_left_strip(artifact_filepath, artifacts_dict, lstrip_paths=None):
  """ Internal helper function to left strip dictionary keys based on
  prefixes passed by the user. """
  if lstrip_paths:
    # If a prefix is passed using the argument --lstrip-paths,
    # that prefix is left stripped from the filepath passed.
    # Note: if the prefix doesn't include a trailing /, the dictionary key
    # may include an unexpected /.
    for prefix in lstrip_paths:
      if artifact_filepath.startswith(prefix):
        artifact_filepath = artifact_filepath[len(prefix):]
        break

    if artifact_filepath in artifacts_dict:
      raise in_toto.exceptions.PrefixError("Prefix selection has "
          "resulted in non unique dictionary key '{}'"
          .format(artifact_filepath))

  return artifact_filepath


def record_artifacts_as_dict(artifacts, exclude_patterns=None,
    base_path=None, follow_symlink_dirs=False, normalize_line_endings=False,
    lstrip_paths=None):
  """
  <Purpose>
    Hashes each file in the passed path list. If the path list contains
    paths to directories the directory tree(s) are traversed.

    The files a link command is executed on are called materials.
    The files that result form a link command execution are called
    products.

    Paths are normalized for matching and storing by left stripping "./"

    NOTE on exclude patterns:
      - Uses PathSpec to compile gitignore-style patterns, making use of the
        GitWildMatchPattern class (registered as 'gitwildmatch')

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

    exclude_patterns: (optional)
            Artifacts matched by the pattern are excluded from the result.
            Exclude patterns can be passed as argument or specified via
            ARTIFACT_EXCLUDE_PATTERNS setting (see `in_toto.settings`) or
            via envvars or rcfiles (see `in_toto.user_settings`).
            If passed, patterns specified via settings are overriden.

    base_path: (optional)
            Change to base_path and record artifacts relative from there.
            If not passed, current working directory is used as base_path.
            NOTE: The base_path part of the recorded artifact is not included
            in the returned paths.

    follow_symlink_dirs: (optional)
            Follow symlinked dirs if the linked dir exists (default is False).
            The recorded path contains the symlink name, not the resolved name.
            NOTE: This parameter toggles following linked directories only,
            linked files are always recorded, independently of this parameter.
            NOTE: Beware of infinite recursions that can occur if a symlink
            points to a parent directory or itself.

    normalize_line_endings: (optional)
            If True, replaces windows and mac line endings with unix line
            endings before hashing the content of the passed files, for
            cross-platform support.

    lstrip_paths: (optional)
            If a prefix path is passed, the prefix is left stripped from
            the path of every artifact that contains the prefix.

  <Exceptions>
    in_toto.exceptions.ValueError,
        if we cannot change to base path directory

    in_toto.exceptions.FormatError,
        if the list of exlcude patterns does not match format
        securesystemslib.formats.NAMES_SCHEMA

  <Side Effects>
    Calls functions to generate cryptographic hashes.

  <Returns>
    A dictionary with file paths as keys and the files' hashes as values.
  """

  artifacts_dict = {}

  if not artifacts:
    return artifacts_dict

  if base_path:
    LOG.info("Overriding setting ARTIFACT_BASE_PATH with passed"
        " base path.")
  else:
    base_path = in_toto.settings.ARTIFACT_BASE_PATH


  # Temporarily change into base path dir if set
  if base_path:
    original_cwd = os.getcwd()
    try:
      os.chdir(base_path)

    except Exception as e:
      six.raise_from(ValueError("Could not use '{}' as base path: '{}'".format(
          base_path, e)), e)

  # Normalize passed paths
  norm_artifacts = []
  for path in artifacts:
    norm_artifacts.append(os.path.normpath(path))

  # Passed exclude patterns take precedence over exclude pattern settings
  if exclude_patterns:
    LOG.info("Overriding setting ARTIFACT_EXCLUDE_PATTERNS with passed"
        " exclude patterns.")
  else:
    # TODO: Do we want to keep the exclude pattern setting?
    exclude_patterns = in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS

  # Apply exclude patterns on the passed artifact paths if available
  if exclude_patterns:
    securesystemslib.formats.NAMES_SCHEMA.check_match(exclude_patterns)
    norm_artifacts = _apply_exclude_patterns(norm_artifacts, exclude_patterns)

  # Check if any of the prefixes passed for left stripping is a left substring
  # of another
  if lstrip_paths:
    for prefix_one, prefix_two in itertools.combinations(lstrip_paths, 2):
      if prefix_one.startswith(prefix_two) or \
          prefix_two.startswith(prefix_one):
        raise in_toto.exceptions.PrefixError("'{}' and '{}' "
            "triggered a left substring error".format(prefix_one, prefix_two))

  # Compile the gitignore-style patterns
  exclude_filter = PathSpec.from_lines('gitwildmatch', exclude_patterns or [])

  # Iterate over remaining normalized artifact paths
  for artifact in norm_artifacts:
    if os.path.isfile(artifact):
      # FIXME: this is necessary to provide consisency between windows
      # filepaths and *nix filepaths. A better solution may be in order
      # though...
      artifact = artifact.replace('\\', '/')
      key = _apply_left_strip(artifact, artifacts_dict, lstrip_paths)
      artifacts_dict[key] = _hash_artifact(artifact,
          normalize_line_endings=normalize_line_endings)

    elif os.path.isdir(artifact):
      for root, dirs, files in os.walk(artifact,
          followlinks=follow_symlink_dirs):
        # Create a list of normalized dirpaths
        dirpaths = []
        for dirname in dirs:
          norm_dirpath = os.path.normpath(os.path.join(root, dirname))
          dirpaths.append(norm_dirpath)

        # Applying exclude patterns on the directory paths returned by walk
        # allows to exclude a subdirectory 'sub' with a pattern 'sub'.
        # If we only applied the patterns below on the subdirectory's
        # containing file paths, we'd have to use a wildcard, e.g.: 'sub*'
        if exclude_patterns:
          dirpaths = _apply_exclude_patterns(dirpaths, exclude_filter)

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
            LOG.info("File '{}' appears to be a broken symlink. Skipping..."
                .format(norm_filepath))

        # Apply exlcude patterns on the normalized file paths returned by walk
        if exclude_patterns:
          filepaths = _apply_exclude_patterns(filepaths, exclude_filter)

        for filepath in filepaths:
          # FIXME: this is necessary to provide consisency between windows
          # filepaths and *nix filepaths. A better solution may be in order
          # though...
          normalized_filepath = filepath.replace("\\", "/")
          key = _apply_left_strip(
              normalized_filepath, artifacts_dict, lstrip_paths)
          artifacts_dict[key] = _hash_artifact(filepath,
              normalize_line_endings=normalize_line_endings)

    # Path is no file and no directory
    else:
      LOG.info("path: {} does not exist, skipping..".format(artifact))


  # Change back to where original current working dir
  if base_path:
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
    OSError:
            The given command is not present or non-executable

    securesystemslib.process.subprocess.TimeoutExpired:
            The execution of the given command times out. The default timeout
            is securesystemslib.settings.SUBPROCESS_TIMEOUT.


  <Side Effects>
    Executes passed command in a subprocess and redirects stdout and stderr
    if specified.

  <Returns>
    - A dictionary containing standard output and standard error of the
      executed command, called by-products.
      Note: If record_streams is False, the dict values are empty strings.
    - The return value of the executed command.
  """
  if record_streams:
    return_code, stdout_str, stderr_str = \
        securesystemslib.process.run_duplicate_streams(link_cmd_args,
            timeout=float(in_toto.settings.LINK_CMD_EXEC_TIMEOUT))

  else:
    process = securesystemslib.process.run(link_cmd_args, check=False,
      timeout=float(in_toto.settings.LINK_CMD_EXEC_TIMEOUT),
      stdout=securesystemslib.process.DEVNULL,
      stderr=securesystemslib.process.DEVNULL)
    stdout_str = stderr_str = ""
    return_code = process.returncode

  return {
      "stdout": stdout_str,
      "stderr": stderr_str,
      "return-value": return_code
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
  link_metadata = in_toto_run(name, ["."], ["."], link_cmd_args,
      record_streams=True)

  filename = FILENAME_FORMAT_SHORT.format(step_name=name)
  LOG.info("Storing unsigned link metadata to '{}'...".format(filename))
  link_metadata.dump(filename)
  return link_metadata


def _check_match_signing_key(signing_key):
  """ Helper method to check if the signing_key has securesystemslib's
  KEY_SCHEMA and the private part is not empty.
  # FIXME: Add private key format check to formats
  """
  securesystemslib.formats.KEY_SCHEMA.check_match(signing_key)
  if not signing_key["keyval"].get("private"):
    raise securesystemslib.exceptions.FormatError(
        "Signing key needs to be a private key.")


def in_toto_run(name, material_list, product_list, link_cmd_args,
    record_streams=False, signing_key=None, gpg_keyid=None,
    gpg_use_default=False, gpg_home=None, exclude_patterns=None,
    base_path=None, compact_json=False, record_environment=False,
    normalize_line_endings=False, lstrip_paths=None, metadata_directory=None):
  """Performs a supply chain step or inspection generating link metadata.

  Executes link_cmd_args, recording paths and hashes of files before and after
  command execution (aka. artifacts) in a link metadata file. The metadata is
  signed with the passed signing_key, a gpg key identified by its ID, or the
  default gpg key. If multiple key arguments are passed, only one key is used
  in above order of precedence. The resulting link file is written to
  ``STEP-NAME.KEYID-PREFIX.link``. If no key argument is passed the link
  metadata is neither signed nor written to disk.

  Arguments:
    name: A unique name to associate link metadata with a step or inspection.

    material_list: A list of artifact paths to be recorded before command
        execution. Directories are traversed recursively.

    product_list: A list of artifact paths to be recorded after command
        execution. Directories are traversed recursively.

    link_cmd_args: A list where the first element is a command and the
        remaining elements are arguments passed to that command.

    record_streams (optional): A boolean indicating if standard output and
        standard error of the link command should be recorded in the link
        metadata in addition to being displayed while the command is executed.

    signing_key (optional): A key used to sign the resulting link metadata. The
        format is securesystemslib.formats.KEY_SCHEMA.

    gpg_keyid (optional): A keyid used to identify a local gpg key used to sign
        the resulting link metadata.

    gpg_use_default (optional): A boolean indicating if the default gpg key
        should be used to sign the resulting link metadata.

    gpg_home (optional): A path to the gpg home directory. If not set the
        default gpg home directory is used.

    exclude_patterns (optional): A list of filename patterns to exclude certain
        files from being recorded as artifacts. See Config docs for details.

    base_path (optional): A path relative to which artifacts are recorded.
        Default is the current working directory.

    compact_json (optional): A boolean indicating if the resulting link
        metadata should be written in the most compact JSON representation.

    record_environment (optional): A boolean indicating if information about
        the environment should be added in the resulting link metadata.

    normalize_line_endings (optional): A boolean indicating if line endings of
        artifacts should be normalized before hashing for cross-platform
        support.

    lstrip_paths (optional): A list of path prefixes used to left-strip
        artifact paths before storing them in the resulting link metadata.

    metadata_directory (optional): A directory path to write the resulting link
        metadata file to. Default destination is the current working directory.

  Raises:
    securesystemslib.exceptions.FormatError: Passed arguments are malformed.

    ValueError: Cannot change to base path directory.

    securesystemslib.exceptions.StorageError: Cannot hash artifacts.

    PrefixError: Left-stripping artifact paths results in non-unique dict keys.

    securesystemslib.process.subprocess.TimeoutExpired: Link command times out.

    IOError, FileNotFoundError, NotADirectoryError, PermissionError:
        Cannot write link metadata.

    securesystemslib.exceptions.CryptoError, \
            securesystemslib.exceptions.UnsupportedAlgorithmError:
        Signing errors.

    ValueError, OSError, securesystemslib.gpg.exceptions.CommandError, \
            securesystemslib.gpg.exceptions.KeyNotFoundError:
        gpg signing errors.

  Side Effects:
    Reads artifact files from disk.
    Runs link command in subprocess.
    Calls system gpg in a subprocess, if a gpg key argument is passed.
    Writes link metadata file to disk, if any key argument is passed.

  Returns:
    A Metablock object that contains the resulting link object.

  """
  LOG.info("Running '{}'...".format(name))

  # Check key formats to fail early
  if signing_key:
    _check_match_signing_key(signing_key)
  if gpg_keyid:
    securesystemslib.formats.KEYID_SCHEMA.check_match(gpg_keyid)

  if exclude_patterns:
    securesystemslib.formats.NAMES_SCHEMA.check_match(exclude_patterns)

  if base_path:
    securesystemslib.formats.PATH_SCHEMA.check_match(base_path)

  if metadata_directory:
    securesystemslib.formats.PATH_SCHEMA.check_match(metadata_directory)

  if material_list:
    LOG.info("Recording materials '{}'...".format(", ".join(material_list)))

  materials_dict = record_artifacts_as_dict(material_list,
      exclude_patterns=exclude_patterns, base_path=base_path,
      follow_symlink_dirs=True, normalize_line_endings=normalize_line_endings,
      lstrip_paths=lstrip_paths)

  if link_cmd_args:
    LOG.info("Running command '{}'...".format(" ".join(link_cmd_args)))
    byproducts = execute_link(link_cmd_args, record_streams)
  else:
    byproducts = {}

  if product_list:
    securesystemslib.formats.PATHS_SCHEMA.check_match(product_list)
    LOG.info("Recording products '{}'...".format(", ".join(product_list)))

  products_dict = record_artifacts_as_dict(product_list,
      exclude_patterns=exclude_patterns, base_path=base_path,
      follow_symlink_dirs=True, normalize_line_endings=normalize_line_endings,
      lstrip_paths=lstrip_paths)

  LOG.info("Creating link metadata...")
  environment = {}
  if record_environment:
    environment['workdir'] = os.getcwd().replace('\\', '/')

  link = in_toto.models.link.Link(name=name,
      materials=materials_dict, products=products_dict, command=link_cmd_args,
      byproducts=byproducts, environment=environment)

  link_metadata = Metablock(signed=link, compact_json=compact_json)

  signature = None
  if signing_key:
    LOG.info("Signing link metadata using passed key...")
    signature = link_metadata.sign(signing_key)

  elif gpg_keyid:
    LOG.info("Signing link metadata using passed GPG keyid...")
    signature = link_metadata.sign_gpg(gpg_keyid, gpg_home=gpg_home)

  elif gpg_use_default:
    LOG.info("Signing link metadata using default GPG key ...")
    signature = link_metadata.sign_gpg(gpg_keyid=None, gpg_home=gpg_home)

  # We need the signature's keyid to write the link to keyid infix'ed filename
  if signature:
    signing_keyid = signature["keyid"]
    filename = FILENAME_FORMAT.format(step_name=name, keyid=signing_keyid)

    if metadata_directory is not None:
      filename = os.path.join(metadata_directory, filename)

    LOG.info("Storing link metadata to '{}'...".format(filename))
    link_metadata.dump(filename)

  return link_metadata


def in_toto_record_start(step_name, material_list, signing_key=None,
    gpg_keyid=None, gpg_use_default=False, gpg_home=None,
    exclude_patterns=None, base_path=None, record_environment=False,
    normalize_line_endings=False, lstrip_paths=None):
  """Generates preliminary link metadata.

  Records paths and hashes of materials in a preliminary link metadata file.
  The metadata is signed with the passed signing_key, a gpg key identified by
  its ID, or the default gpg key. If multiple key arguments are passed, only
  one key is used in above order of precedence. At least one key argument must
  be passed. The resulting link file is written to
  ``.STEP-NAME.KEYID-PREFIX.link-unfinished``.

  Use this function together with in_toto_record_stop as an alternative to
  in_toto_run, in order to provide evidence for supply chain steps that cannot
  be carried out by a single command.

  Arguments:
    step_name: A unique name to associate link metadata with a step.

    material_list: A list of artifact paths to be recorded as materials.
        Directories are traversed recursively.

    signing_key (optional): A key used to sign the resulting link metadata. The
        format is securesystemslib.formats.KEY_SCHEMA.

    gpg_keyid (optional): A keyid used to identify a local gpg key used to sign
        the resulting link metadata.

    gpg_use_default (optional): A boolean indicating if the default gpg key
        should be used to sign the resulting link metadata.

    gpg_home (optional): A path to the gpg home directory. If not set the
        default gpg home directory is used.

    exclude_patterns (optional): A list of filename patterns to exclude certain
        files from being recorded as artifacts. See Config docs for details.

    base_path (optional): A path relative to which artifacts are recorded.
        Default is the current working directory.

    record_environment (optional): A boolean indicating if information about
        the environment should be added in the resulting link metadata.

    normalize_line_endings (optional): A boolean indicating if line endings of
        artifacts should be normalized before hashing for cross-platform
        support.

    lstrip_paths (optional): A list of path prefixes used to left-strip
        artifact paths before storing them in the resulting link metadata.

  Raises:
    securesystemslib.exceptions.FormatError: Passed arguments are malformed.

    ValueError: None of signing_key, gpg_keyid or gpg_use_default=True is
        passed.

    securesystemslib.exceptions.StorageError: Cannot hash artifacts.

    PrefixError: Left-stripping artifact paths results in non-unique dict keys.

    securesystemslib.process.subprocess.TimeoutExpired: Link command times out.

    IOError, PermissionError:
        Cannot write link metadata.

    securesystemslib.exceptions.CryptoError, \
            securesystemslib.exceptions.UnsupportedAlgorithmError:
        Signing errors.

    ValueError, OSError, securesystemslib.gpg.exceptions.CommandError, \
            securesystemslib.gpg.exceptions.KeyNotFoundError:
        gpg signing errors.

  Side Effects:
    Reads artifact files from disk.
    Calls system gpg in a subprocess, if a gpg key argument is passed.
    Writes preliminary link metadata file to disk.

  """
  LOG.info("Start recording '{}'...".format(step_name))

  # Fail if there is no signing key arg at all
  if not signing_key and not gpg_keyid and not gpg_use_default:
    raise ValueError("Pass either a signing key, a gpg keyid or set"
        " gpg_use_default to True!")

  # Check key formats to fail early
  if signing_key:
    _check_match_signing_key(signing_key)
  if gpg_keyid:
    securesystemslib.formats.KEYID_SCHEMA.check_match(gpg_keyid)

  if exclude_patterns:
    securesystemslib.formats.NAMES_SCHEMA.check_match(exclude_patterns)

  if base_path:
    securesystemslib.formats.PATH_SCHEMA.check_match(base_path)

  if material_list:
    LOG.info("Recording materials '{}'...".format(", ".join(material_list)))

  materials_dict = record_artifacts_as_dict(material_list,
      exclude_patterns=exclude_patterns, base_path=base_path,
      follow_symlink_dirs=True, normalize_line_endings=normalize_line_endings,
      lstrip_paths=lstrip_paths)

  LOG.info("Creating preliminary link metadata...")
  environment = {}
  if record_environment:
    environment['workdir'] = os.getcwd().replace('\\', '/')

  link = in_toto.models.link.Link(name=step_name,
          materials=materials_dict, products={}, command=[], byproducts={},
          environment=environment)

  link_metadata = Metablock(signed=link)

  if signing_key:
    LOG.info("Signing link metadata using passed key...")
    signature = link_metadata.sign(signing_key)

  elif gpg_keyid:
    LOG.info("Signing link metadata using passed GPG keyid...")
    signature = link_metadata.sign_gpg(gpg_keyid, gpg_home=gpg_home)

  else:  # (gpg_use_default)
    LOG.info("Signing link metadata using default GPG key ...")
    signature = link_metadata.sign_gpg(gpg_keyid=None, gpg_home=gpg_home)

  # We need the signature's keyid to write the link to keyid infix'ed filename
  signing_keyid = signature["keyid"]

  unfinished_fn = UNFINISHED_FILENAME_FORMAT.format(step_name=step_name,
    keyid=signing_keyid)

  LOG.info(
      "Storing preliminary link metadata to '{}'...".format(unfinished_fn))
  link_metadata.dump(unfinished_fn)



def in_toto_record_stop(step_name, product_list, signing_key=None,
    gpg_keyid=None, gpg_use_default=False, gpg_home=None,
    exclude_patterns=None, base_path=None, normalize_line_endings=False,
    lstrip_paths=None, metadata_directory=None):
  """Finalizes preliminary link metadata generated with in_toto_record_start.

  Loads preliminary link metadata file, verifies its signature, and records
  paths and hashes as products, thus finalizing the link metadata. The metadata
  is signed with the passed signing_key, a gpg key identified by its ID, or the
  default gpg key. If multiple key arguments are passed, only one key is used
  in above order of precedence. At least one key argument must be passed and it
  must be the same as the one used to sign the preliminary link metadata file.
  The resulting link file is written to ``STEP-NAME.KEYID-PREFIX.link``.

  Use this function together with in_toto_record_start as an alternative to
  in_toto_run, in order to provide evidence for supply chain steps that cannot
  be carried out by a single command.

  Arguments:
    step_name: A unique name to associate link metadata with a step.

    product_list: A list of artifact paths to be recorded as products.
        Directories are traversed recursively.

    signing_key (optional): A key used to sign the resulting link metadata. The
        format is securesystemslib.formats.KEY_SCHEMA.

    gpg_keyid (optional): A keyid used to identify a local gpg key used to sign
        the resulting link metadata.

    gpg_use_default (optional): A boolean indicating if the default gpg key
        should be used to sign the resulting link metadata.

    gpg_home (optional): A path to the gpg home directory. If not set the
        default gpg home directory is used.

    exclude_patterns (optional): A list of filename patterns to exclude certain
        files from being recorded as artifacts.

    base_path (optional): A path relative to which artifacts are recorded.
        Default is the current working directory.

    normalize_line_endings (optional): A boolean indicating if line endings of
        artifacts should be normalized before hashing for cross-platform
        support.

    lstrip_paths (optional): A list of path prefixes used to left-strip
        artifact paths before storing them in the resulting link metadata.

    metadata_directory (optional): A directory path to write the resulting link
        metadata file to. Default destination is the current working directory.

  Raises:
    securesystemslib.exceptions.FormatError: Passed arguments are malformed.

    ValueError: None of signing_key, gpg_keyid or gpg_use_default=True is
        passed.

    LinkNotFoundError: No preliminary link metadata file found.

    securesystemslib.exceptions.StorageError: Cannot hash artifacts.

    PrefixError: Left-stripping artifact paths results in non-unique dict keys.

    securesystemslib.process.subprocess.TimeoutExpired: Link command times out.

    IOError, FileNotFoundError, NotADirectoryError, PermissionError:
        Cannot write link metadata.

    securesystemslib.exceptions.CryptoError, \
            securesystemslib.exceptions.UnsupportedAlgorithmError:
        Signing errors.

    ValueError, OSError, securesystemslib.gpg.exceptions.CommandError, \
            securesystemslib.gpg.exceptions.KeyNotFoundError:
        gpg signing errors.

  Side Effects:
    Reads preliminary link metadata file from disk.
    Reads artifact files from disk.
    Calls system gpg in a subprocess, if a gpg key argument is passed.
    Writes resulting link metadata file to disk.
    Removes preliminary link metadata file from disk.

  """
  LOG.info("Stop recording '{}'...".format(step_name))

  # Check that we have something to sign and if the formats are right
  if not signing_key and not gpg_keyid and not gpg_use_default:
    raise ValueError("Pass either a signing key, a gpg keyid or set"
        " gpg_use_default to True")

  if signing_key:
    _check_match_signing_key(signing_key)
  if gpg_keyid:
    securesystemslib.formats.KEYID_SCHEMA.check_match(gpg_keyid)

  if exclude_patterns:
    securesystemslib.formats.NAMES_SCHEMA.check_match(exclude_patterns)

  if base_path:
    securesystemslib.formats.PATH_SCHEMA.check_match(base_path)

  if metadata_directory:
    securesystemslib.formats.PATH_SCHEMA.check_match(metadata_directory)

  # Load preliminary link file
  # If we have a signing key we can use the keyid to construct the name
  if signing_key:
    unfinished_fn = UNFINISHED_FILENAME_FORMAT.format(step_name=step_name,
        keyid=signing_key["keyid"])

  # FIXME: Currently there is no way to know the default GPG key's keyid and
  # so we glob for preliminary link files
  else:
    unfinished_fn_glob = UNFINISHED_FILENAME_FORMAT_GLOB.format(
        step_name=step_name, pattern="*")
    unfinished_fn_list = glob.glob(unfinished_fn_glob)

    if not len(unfinished_fn_list):
      raise in_toto.exceptions.LinkNotFoundError("Could not find a preliminary"
          " link for step '{}' in the current working directory.".format(
          step_name))

    if len(unfinished_fn_list) > 1:
      raise in_toto.exceptions.LinkNotFoundError("Found more than one"
          " preliminary links for step '{}' in the current working directory:"
          " {}. We need exactly one to stop recording.".format(
          step_name, ", ".join(unfinished_fn_list)))

    unfinished_fn = unfinished_fn_list[0]

  LOG.info("Loading preliminary link metadata '{}'...".format(unfinished_fn))
  link_metadata = Metablock.load(unfinished_fn)

  # The file must have been signed by the same key
  # If we have a signing_key we use it for verification as well
  if signing_key:
    LOG.info(
        "Verifying preliminary link signature using passed signing key...")
    keyid = signing_key["keyid"]
    verification_key = signing_key

  elif gpg_keyid:
    LOG.info("Verifying preliminary link signature using passed gpg key...")
    gpg_pubkey = securesystemslib.gpg.functions.export_pubkey(
        gpg_keyid, gpg_home)
    keyid = gpg_pubkey["keyid"]
    verification_key = gpg_pubkey

  else: # must be gpg_use_default
    # FIXME: Currently there is no way to know the default GPG key's keyid
    # before signing. As a workaround we extract the keyid of the preliminary
    # Link file's signature and try to export a pubkey from the gpg
    # home directory. We do this even if a gpg_keyid was specified, because gpg
    # accepts many different ids (mail, name, parts of an id, ...) but we
    # need a specific format.
    LOG.info("Verifying preliminary link signature using default gpg key...")
    keyid = link_metadata.signatures[0]["keyid"]
    gpg_pubkey = securesystemslib.gpg.functions.export_pubkey(
        keyid, gpg_home)
    verification_key = gpg_pubkey

  link_metadata.verify_signature(verification_key)

  # Record products if a product path list was passed
  if product_list:
    LOG.info("Recording products '{}'...".format(", ".join(product_list)))

  link_metadata.signed.products = record_artifacts_as_dict(
      product_list, exclude_patterns=exclude_patterns, base_path=base_path,
      follow_symlink_dirs=True, normalize_line_endings=normalize_line_endings,
      lstrip_paths=lstrip_paths)

  link_metadata.signatures = []
  if signing_key:
    LOG.info("Updating signature with key '{:.8}...'...".format(keyid))
    link_metadata.sign(signing_key)

  else: # gpg_keyid or gpg_use_default
    # In both cases we use the keyid we got from verifying the preliminary
    # link signature above.
    LOG.info("Updating signature with gpg key '{:.8}...'...".format(keyid))
    link_metadata.sign_gpg(keyid, gpg_home)

  fn = FILENAME_FORMAT.format(step_name=step_name, keyid=keyid)

  if metadata_directory is not None:
    fn = os.path.join(metadata_directory, fn)

  LOG.info("Storing link metadata to '{}'...".format(fn))
  link_metadata.dump(fn)

  LOG.info("Removing unfinished link metadata '{}'...".format(unfinished_fn))
  os.remove(unfinished_fn)
