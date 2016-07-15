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

import toto.ssl_crypto.hash
import toto.ssl_crypto.keys
import toto.ssl_crypto.formats



def record_file_state(link_files):
  """Takes a directory or file names as input and creates a hash. 
  The dir/files a link command is executed on are called material. The dir/files
  the result form a link command execution are called product."""

  hash_list = []
  for root, dirs, files in os.walk(link_files):
    for name in files:
      digest_object = toto.ssl_crypto.hash.digest_filename(
          os.path.join(root, name))
      hash_list.append(digest_object.hexdigest())

  return hash_list


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


def create_link_metadata(material_hash, product_hash, by_products):
  """Takes the state of the material (before link command execution), the state
  of the product (after link command execution) and the by-products of the link
  command execution and creates the link metadata according to the specified 
  metadata format."""

  return {
      "material" : material_hash,
      "product" : product_hash,
      "by_product" : by_products 
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


def run_link(material, toto_cmd_args, product):
  """ Performs all actions associated with toto run-link.
  XXX: This should probably be atomic, i.e. all or nothing"""

  material_hashes = record_file_state(material)

  by_products = execute_link(toto_cmd_args)

  product_hashes = record_file_state(product)

  # XXX: This is not going to happen here
  if (material_hashes == product_hashes):
    print "This was of type report"
  else:
    print "This was of type transform"

  link_metadata = create_link_metadata(material_hashes, product_hashes, by_products)

  # XXX: This is not going to happen here, we need some PKI
  test_key = toto.util.get_key()

  signed_link_metadata = sign_link_metadata(link_metadata, test_key)

  # XXX: This is not going to happen here!!!!
  print toto.verifylib._verify_metadata_signature(
    test_key,
    signed_link_metadata["signatures"][0],
    )

  store_link_metadata(signed_link_metadata)


  