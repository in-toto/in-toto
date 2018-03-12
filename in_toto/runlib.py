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
import fnmatch
import glob
import logging

import in_toto.settings
import in_toto.exceptions
from in_toto.models.link import (UNFINISHED_FILENAME_FORMAT, FILENAME_FORMAT,
    FILENAME_FORMAT_SHORT, UNFINISHED_FILENAME_FORMAT_GLOB)

import securesystemslib.formats
import securesystemslib.hash
import securesystemslib.exceptions

from in_toto.models.metadata import Metablock


# Inherits from in_toto base logger (c.f. in_toto.log)
log = logging.getLogger(__name__)


# POSIX users (Linux, BSD, etc.) are strongly encouraged to
# install and use the much more recent subprocess32
if os.name == 'posix' and sys.version_info[0] < 3: # pragma: no cover
  try:
    import subprocess32 as subprocess
  except ImportError:
    log.warning("POSIX users (Linux, BSD, etc.) are strongly encouraged to"
        " install and use the much more recent subprocess32")
    import subprocess
else: # pragma: no cover
  import subprocess


def _hash_artifact(filepath, hash_algorithms=None):
  """Internal helper that takes a filename and hashes the respective file's
  contents using the passed hash_algorithms and returns a hashdict conformant
  with securesystemslib.formats.HASHDICT_SCHEMA. """
  if not hash_algorithms:
    hash_algorithms = ['sha256']

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


def record_artifacts_as_dict(artifacts, exclude_patterns=None,
    base_path=None, follow_symlink_dirs=False):
  """
  <Purpose>
    Hashes each file in the passed path list. If the path list contains
    paths to directories the directory tree(s) are traversed.

    The files a link command is executed on are called materials.
    The files that result form a link command execution are called
    products.

    Paths are normalized for matching and storing by left stripping "./"

    NOTE on exclude patterns:
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
    log.info("Overriding setting ARTIFACT_BASE_PATH with passed"
        " base path.")
  else:
    base_path = in_toto.settings.ARTIFACT_BASE_PATH


  # Temporarily change into base path dir if set
  if base_path:
    original_cwd = os.getcwd()
    try:
      os.chdir(base_path)

    except Exception as e:
      raise ValueError("Could not use '{}' as base path: '{}'".format(
          base_path, e))

  # Normalize passed paths
  norm_artifacts = []
  for path in artifacts:
    norm_artifacts.append(os.path.normpath(path))

  # Passed exclude patterns take precedence over exclude pattern settings
  if exclude_patterns:
    log.info("Overriding setting ARTIFACT_EXCLUDE_PATTERNS with passed"
        " exclude patterns.")
  else:
    # TODO: Do we want to keep the exclude pattern setting?
    exclude_patterns = in_toto.settings.ARTIFACT_EXCLUDE_PATTERNS

  # Apply exclude patterns on the passed artifact paths if available
  if exclude_patterns:
    securesystemslib.formats.NAMES_SCHEMA.check_match(exclude_patterns)
    norm_artifacts = _apply_exclude_patterns(norm_artifacts, exclude_patterns)

  # Iterate over remaining normalized artifact paths
  for artifact in norm_artifacts:
    if os.path.isfile(artifact):
      # Path was already normalized above
      artifacts_dict[artifact] = _hash_artifact(artifact)

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
          dirpaths = _apply_exclude_patterns(dirpaths, exclude_patterns)

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
            log.info("File '{}' appears to be a broken symlink. Skipping..."
                .format(norm_filepath))

        # Apply exlcude patterns on the normalized file paths returned by walk
        if exclude_patterns:
          filepaths = _apply_exclude_patterns(filepaths, exclude_patterns)

        for filepath in filepaths:
          artifacts_dict[filepath] = _hash_artifact(filepath)

    # Path is no file and no directory
    else:
      log.info("path: {} does not exist, skipping..".format(artifact))


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
    TBA (see https://github.com/in-toto/in-toto/issues/6)

  <Side Effects>
    Executes passed command in a subprocess and redirects stdout and stderr
    if specified.

  <Returns>
    - A dictionary containing standard output and standard error of the
      executed command, called by-products.
      Note: If record_streams is False, the dict values are empty strings.
    - The return value of the executed command.
  """
  # TODO: Properly duplicate standard streams (issue #11)
  if record_streams:
    process = subprocess.Popen(link_cmd_args, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, universal_newlines=True)

    stdout_str, stderr_str = process.communicate()
    return_value = process.returncode

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
  link_metadata = in_toto_run(name, ["."], ["."], link_cmd_args,
      record_streams=True)

  filename = FILENAME_FORMAT_SHORT.format(step_name=name)
  log.info("Storing unsigned link metadata to '{}'...".format(filename))
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
    base_path=None):
  """
  <Purpose>
    Calls functions in this module to run the command passed as link_cmd_args
    argument and to store materials, products, by-products and environment
    information into a link metadata file.

    The link metadata file is signed either with the passed signing_key, or
    a gpg key identified by the passed gpg_keyid or with the default gpg
    key if gpg_use_default is True.

    Even if multiple key parameters are passed, only one key is used for
    signing (in above order of precedence).

    The link file is dumped to `link.FILENAME_FORMAT` using the signing key's
    keyid.

    If no key parameter is passed the link is neither signed nor dumped.

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
    record_streams: (optional)
            A bool that specifies whether to redirect standard output and
            and standard error to a temporary file which is returned to the
            caller (True) or not (False).
    signing_key: (optional)
            If not None, link metadata is signed with this key.
            Format is securesystemslib.formats.KEY_SCHEMA
    gpg_keyid: (optional)
            If not None, link metadata is signed with a gpg key identified
            by the passed keyid.
    gpg_use_default: (optional)
            If True, link metadata is signed with default gpg key.
    gpg_home: (optional)
            Path to GPG keyring (if not set the default keyring is used).
    exclude_patterns: (optional)
            Artifacts matched by the pattern are excluded from the materials
            and products sections in the resulting link.
    base_path: (optional)
            If passed, record artifacts relative to base_path. Default is
            current working directory.
            NOTE: The base_path part of the recorded material is not included
            in the resulting preliminary link's material/product sections.

  <Exceptions>
    securesystemslib.FormatError if a signing_key is passed and does not match
        securesystemslib.formats.KEY_SCHEMA or a gpg_keyid is passed and does
        not match securesystemslib.formats.KEYID_SCHEMA or exclude_patterns
        are passed and don't match securesystemslib.formats.NAMES_SCHEMA, or
        base_path is passed and does not match
        securesystemslib.formats.PATH_SCHEMA or is not a directory.

  <Side Effects>
    If a key parameter is passed for signing, the newly created link metadata
    file is written to disk using the filename scheme: `link.FILENAME_FORMAT`

  <Returns>
    Newly created Metablock object containing a Link object

  """
  log.info("Running '{}'...".format(name))

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
    log.info("Recording materials '{}'...".format(", ".join(material_list)))

  materials_dict = record_artifacts_as_dict(material_list,
      exclude_patterns=exclude_patterns, base_path=base_path,
      follow_symlink_dirs=True)

  if link_cmd_args:
    log.info("Running command '{}'...".format(" ".join(link_cmd_args)))
    byproducts = execute_link(link_cmd_args, record_streams)
  else:
    byproducts = {}

  if product_list:
    log.info("Recording products '{}'...".format(", ".join(product_list)))

  products_dict = record_artifacts_as_dict(product_list,
      exclude_patterns=exclude_patterns, base_path=base_path,
      follow_symlink_dirs=True)

  log.info("Creating link metadata...")
  link = in_toto.models.link.Link(name=name,
      materials=materials_dict, products=products_dict, command=link_cmd_args,
      byproducts=byproducts, environment={"workdir": os.getcwd()})

  link_metadata = Metablock(signed=link)

  signature = None
  if signing_key:
    log.info("Signing link metadata using passed key...")
    signature = link_metadata.sign(signing_key)

  elif gpg_keyid:
    log.info("Signing link metadata using passed GPG keyid...")
    signature = link_metadata.sign_gpg(gpg_keyid, gpg_home=gpg_home)

  elif gpg_use_default:
    log.info("Signing link metadata using default GPG key ...")
    signature = link_metadata.sign_gpg(gpg_keyid=None, gpg_home=gpg_home)

  # We need the signature's keyid to write the link to keyid infix'ed filename
  if signature:
    signing_keyid = signature["keyid"]
    filename = FILENAME_FORMAT.format(step_name=name, keyid=signing_keyid)
    log.info("Storing link metadata to '{}'...".format(filename))
    link_metadata.dump(filename)

  return link_metadata


def in_toto_record_start(step_name, material_list, signing_key=None,
    gpg_keyid=None, gpg_use_default=False, gpg_home=None,
    exclude_patterns=None, base_path=None):
  """
  <Purpose>
    Starts creating link metadata for a multi-part in-toto step. I.e.
    records passed materials, creates link meta data object from it, signs it
    with passed signing_key, gpg key identified by the passed gpg_keyid
    or the default gpg key and stores it to disk under
    UNFINISHED_FILENAME_FORMAT.

    One of signing_key, gpg_keyid or gpg_use_default has to be passed.

  <Arguments>
    step_name:
            A unique name to relate link metadata with a step defined in the
            layout.
    material_list:
            List of file or directory paths that should be recorded as
            materials.
    signing_key: (optional)
            If not None, link metadata is signed with this key.
            Format is securesystemslib.formats.KEY_SCHEMA
    gpg_keyid: (optional)
            If not None, link metadata is signed with a gpg key identified
            by the passed keyid.
    gpg_use_default: (optional)
            If True, link metadata is signed with default gpg key.
    gpg_home: (optional)
            Path to GPG keyring (if not set the default keyring is used).
    exclude_patterns: (optional)
            Artifacts matched by the pattern are excluded from the materials
            section in the resulting preliminary link.
    base_path: (optional)
            If passed, record materials relative to base_path. Default is
            current working directory.
            NOTE: The base_path part of the recorded materials is not included
            in the resulting preliminary link's material section.

  <Exceptions>
    ValueError if none of signing_key, gpg_keyid or gpg_use_default=True
        is passed.

    securesystemslib.FormatError if a signing_key is passed and does not match
        securesystemslib.formats.KEY_SCHEMA or a gpg_keyid is passed and does
        not match securesystemslib.formats.KEYID_SCHEMA or exclude_patterns
        are passed and don't match securesystemslib.formats.NAMES_SCHEMA, or
        base_path is passed and does not match
        securesystemslib.formats.PATH_SCHEMA or is not a directory.

  <Side Effects>
    Writes newly created link metadata file to disk using the filename scheme
    from link.UNFINISHED_FILENAME_FORMAT

  <Returns>
    None.

  """
  log.info("Start recording '{}'...".format(step_name))

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
    log.info("Recording materials '{}'...".format(", ".join(material_list)))

  materials_dict = record_artifacts_as_dict(material_list,
      exclude_patterns=exclude_patterns, base_path=base_path,
      follow_symlink_dirs=True)

  log.info("Creating preliminary link metadata...")
  link = in_toto.models.link.Link(name=step_name,
          materials=materials_dict, products={}, command=[], byproducts={},
          environment={"workdir": os.getcwd()})

  link_metadata = Metablock(signed=link)

  if signing_key:
    log.info("Signing link metadata using passed key...")
    signature = link_metadata.sign(signing_key)

  elif gpg_keyid:
    log.info("Signing link metadata using passed GPG keyid...")
    signature = link_metadata.sign_gpg(gpg_keyid, gpg_home=gpg_home)

  else:  # (gpg_use_default)
    log.info("Signing link metadata using default GPG key ...")
    signature = link_metadata.sign_gpg(gpg_keyid=None, gpg_home=gpg_home)

  # We need the signature's keyid to write the link to keyid infix'ed filename
  signing_keyid = signature["keyid"]

  unfinished_fn = UNFINISHED_FILENAME_FORMAT.format(step_name=step_name,
    keyid=signing_keyid)

  log.info("Storing preliminary link metadata to '{}'...".format(unfinished_fn))
  link_metadata.dump(unfinished_fn)



def in_toto_record_stop(step_name, product_list, signing_key=None,
    gpg_keyid=None, gpg_use_default=False, gpg_home=None,
    exclude_patterns=None, base_path=None):
  """
  <Purpose>
    Finishes creating link metadata for a multi-part in-toto step.
    Loads unfinished link metadata file from disk, verifies
    that the file was signed with either the passed signing key, a gpg key
    identified by the passed gpg_keyid or the default gpg key.

    Then records products, updates unfinished Link object
    (products and signature), removes unfinished link file from and
    stores new link file to disk.

    One of signing_key, gpg_keyid or gpg_use_default has to be passed and it
    needs to be the same that was used with preceding in_toto_record_start.

  <Arguments>
    step_name:
            A unique name to relate link metadata with a step defined in the
            layout.
    product_list:
            List of file or directory paths that should be recorded as products.
    signing_key: (optional)
            If not None, link metadata is signed with this key.
            Format is securesystemslib.formats.KEY_SCHEMA
    gpg_keyid: (optional)
            If not None, link metadata is signed with a gpg key identified
            by the passed keyid.
    gpg_use_default: (optional)
            If True, link metadata is signed with default gpg key.
    gpg_home: (optional)
            Path to GPG keyring (if not set the default keyring is used).
    exclude_patterns: (optional)
            Artifacts matched by the pattern are excluded from the products
            sections in the resulting link.
    base_path: (optional)
            If passed, record products relative to base_path. Default is
            current working directory.
            NOTE: The base_path part of the recorded products is not included
            in the resulting preliminary link's product section.

  <Exceptions>
    ValueError if none of signing_key, gpg_keyid or gpg_use_default=True
        is passed.

    securesystemslib.FormatError if a signing_key is passed and does not match
        securesystemslib.formats.KEY_SCHEMA or a gpg_keyid is passed and does
        not match securesystemslib.formats.KEYID_SCHEMA, or exclude_patterns
        are passed and don't match securesystemslib.formats.NAMES_SCHEMA, or
        base_path is passed and does not match
        securesystemslib.formats.PATH_SCHEMA or is not a directory.

    LinkNotFoundError if gpg is used for signing and the corresponding
        preliminary link file can not be found in the current working directory

  <Side Effects>
    Writes newly created link metadata file to disk using the filename scheme
    from link.FILENAME_FORMAT
    Removes unfinished link file link.UNFINISHED_FILENAME_FORMAT from disk

  <Returns>
    None.

  """
  log.info("Stop recording '{}'...".format(step_name))

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

  log.info("Loading preliminary link metadata '{}'...".format(unfinished_fn))
  link_metadata = Metablock.load(unfinished_fn)

  # The file must have been signed by the same key
  # If we have a signing_key we use it for verification as well
  if signing_key:
    log.info("Verifying preliminary link signature using passed signing key...")
    keyid = signing_key["keyid"]
    verification_key = signing_key

  elif gpg_keyid:
    log.info("Verifying preliminary link signature using passed gpg key...")
    gpg_pubkey = in_toto.gpg.functions.gpg_export_pubkey(gpg_keyid, gpg_home)
    keyid = gpg_pubkey["keyid"]
    verification_key = gpg_pubkey

  else: # must be gpg_use_default
    # FIXME: Currently there is no way to know the default GPG key's keyid
    # before signing. As a workaround we extract the keyid of the preliminary
    # Link file's signature and try to export a pubkey from the gpg
    # keyring. We do this even if a gpg_keyid was specified, because gpg
    # accepts many different ids (mail, name, parts of an id, ...) but we
    # need a specific format.
    log.info("Verifying preliminary link signature using default gpg key...")
    keyid = link_metadata.signatures[0]["keyid"]
    gpg_pubkey = in_toto.gpg.functions.gpg_export_pubkey(keyid, gpg_home)
    verification_key = gpg_pubkey

  link_metadata.verify_signature(verification_key)

  # Record products if a product path list was passed
  if product_list:
    log.info("Recording products '{}'...".format(", ".join(product_list)))

  link_metadata.signed.products = record_artifacts_as_dict(product_list,
      exclude_patterns=exclude_patterns, base_path=base_path,
      follow_symlink_dirs=True)

  link_metadata.signatures = []
  if signing_key:
    log.info("Updating signature with key '{:.8}...'...".format(keyid))
    link_metadata.sign(signing_key)

  else: # gpg_keyid or gpg_use_default
    # In both cases we use the keyid we got from verifying the preliminary
    # link signature above.
    log.info("Updating signature with gpg key '{:.8}...'...".format(keyid))
    link_metadata.sign_gpg(keyid, gpg_home)

  fn = FILENAME_FORMAT.format(step_name=step_name, keyid=keyid)
  log.info("Storing link metadata to '{}'...".format(fn))
  link_metadata.dump(fn)

  log.info("Removing unfinished link metadata '{}'...".format(unfinished_fn))
  os.remove(unfinished_fn)
