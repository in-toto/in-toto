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
  Provide a wrapper for any command of the software supply chain.

  The wrapper performs the following tasks which are also implementes in this
  library.

    * Record state of material (files the command is executed on)
    * Execute command
    * Capture stdout/stderr/return value of the executed command
    * Record state of product (files after the command was executed)
    * Create metadata file
    * Sign metadata file


  TODO
    * Decide on metadata format
    * Decide on metadata location

"""
import sys
import os
import tempfile
import toto.verifylib

import toto.util

# POSIX users (Linux, BSD, etc.) are strongly encouraged to 
# install and use the much more recent subprocess32
if os.name == 'posix' and sys.version_info[0] < 3:
  import subprocess32 as subprocess
else:
  import subprocess

import toto.formats

import toto.ssl_crypto.hash
import toto.ssl_crypto.keys
import toto.ssl_crypto.formats


def record_link_state(link_files):
  """Takes a directory or file names as input and creates a list of 
  dictionaries with filepaths as keys and file hashes as key.

  The dir/files a link command is executed on are called material. The dir/files
  the result form a link command execution are called product."""

  link_state_list = []
  for root, dirs, files in os.walk(link_files):
    for name in files:
      filename = os.path.join(root, name)

      # Create new digest object for each file
      digest_object = toto.ssl_crypto.hash.digest_filename(filename)
      link_state_entry = {filename : digest_object.hexdigest()}
      link_state_list.append(link_state_entry)

  # XXX: Should we do checking here?
  toto.formats.LINK_STATE_SCHEMA

  return link_state_list


def execute_link(link_cmd_args):
  """Takes a command and its options and arguments of the software supply 
  chain as input, runs the command in a suprocess, records the stdout and 
  stderr and return value of the command and returns them. Stdout, stderr and 
  return value are called by_products."""

  # XXX: Use SpooledTemporaryFile if we expect very large outputs
  stdout_file = tempfile.TemporaryFile()
  stderr_file = tempfile.TemporaryFile()

  ret_val = subprocess.call(link_cmd_args, stdout=stdout_file, stderr=stderr_file)

  stdout_file.seek(0)
  stderr_file.seek(0)

  stdout_str = stdout_file.read()
  stderr_str = stderr_file.read()

  return (stdout_str, stderr_str, ret_val)


def create_link_metadata(command, materials_hash, transformations, 
    transformations_hash, report):
  """Takes the state of the material (before link command execution), the state
  of the product (after link command execution) and the by-products of the link
  command execution and creates the link metadata according to the specified 
  metadata format.

  XXX: Maybe we want to define a class for this
  toto/models.py would be a good place"""

  return {
    "_type" : "link",
    # "version" : 
    "command" : command
    "materials-hash" : material_hash,
    "transformations" : transformations,
    "transformations-hash" : transformations_hash,
    "report" : report
  }


def sign_link_metadata(link_metadata, functionary_key):
  """Takes link metadata and the key of the functionary who executed the 
  according link command and signs the metadata."""

  
  signable = toto.ssl_crypto.formats.make_signable(link_metadata)
  sig = toto.ssl_crypto.keys.create_signature(functionary_key, link_metadata)

  signable['signatures'].append(sig)

  return signable


def store_link_metadata(signed_link_metadata):
  """Store link metadata to a file."""
  pass


def create_transformations(materials_state, products_state):
  """Creates transformations list, which lists the subset of the union of
  materials and in case they were added, transformed or removed.
  The format is:
  [ {PATH: [ACTION, HASH]}, ...] 
  If ACTION is "add" or "transform" then HASH is the hash of the product
  If ACTION is "remove" then HASH is the hash of the material
  """

  materials_paths = set(materials_state.keys())
  products_paths = set(products_state.keys())

  transformations = []

  # Removed files
  for path in materials_paths - products_paths:
    transformations.append({path : ["remove", materials_state[path]]})

  # Added files
  for path in products_paths - materials_paths:
    transformations.append({path : ["add", products_state[path]]})

  # Transformed files
  for path in materials_paths.intersection(products_paths):
    if materials_state[path] != products_state[path]:
      transformations.append({path : ["transform", products_state[path]]})

  return transformations


def create_hash_from_link_state(link_state):
  """Creates hash from link state python object string representation"""

  link_state_repr = repr(link_state)
  digest_object = toto.ssl_crypto.hash.digest()
  digest_object.update(link_state_repr)
  link_state_hash = digest_object.hexdigest()

  return link_state_hash




def run_link(material, toto_cmd_args, product):
  """Performs all actions associated with toto run-link.
  XXX: This should probably be atomic, i.e. all or nothing"""

  # Perform arguments schema checking
  toto_cmd_args.check_match()

  # Record - Run - Record
  materials_state = record_link_state(material)
  report = execute_link(toto_cmd_args)
  products_state = record_link_state(product)

  # Create one hash from all material hashes 
  materials_hash = create_hash_from_link_state(materials_state)

  # XXX: I think transfomrations_hash should rather be called products_hash
  transformations_hash = create_hash_from_link_state(products_state)

  transformations = create_transformations(materials_state, products_state)

  link_metadata = create_link_metadata(toto_cmd_args, materials_hash, 
      transformations, transformations_hash, report)

  # XXX: This is not going to happen here, we need some PKI
  test_key = toto.util.get_key()

  signed_link_metadata = sign_link_metadata(link_metadata, test_key)

  # XXX: This is not going to happen here!!!!
  print toto.verifylib._verify_metadata_signature(
    test_key,
    signed_link_metadata["signatures"][0],
    )

  store_link_metadata(signed_link_metadata)


  