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

    * Record state of material (files the command is executed on)
    * Execute command
      * Capture stdout/stderr/return value of the executed command
    * Record state of product (files after the command was executed)
    * Create metadata file
    * Sign metadata file
    * Store medata file as "[name].link"

  TODO
    * Decide on metadata location

"""
import sys
import os
import tempfile

# POSIX users (Linux, BSD, etc.) are strongly encouraged to 
# install and use the much more recent subprocess32
if os.name == 'posix' and sys.version_info[0] < 3:
  import subprocess32 as subprocess
else:
  import subprocess

# XXX LP: I think we'll get rid of toto formats because we want to use
# model validators instead for toto schemas, we'll still use
# toto.ssl_crypto.formats though

# import toto.formats

import toto.models.link

import toto.ssl_crypto.hash
import toto.ssl_crypto.keys
import toto.ssl_crypto.formats


def record_artifacts_as_dict(artifacts):
  """Takes a directory or file names as input and creates a dict
  with filepaths as keys and their file's hashes as values.

  The dirs/files a link command is executed on are called materials.
  The dir/files the result form a link command execution are called products.

  XXX Todo: Needs revision!
  """
  artifacts_dict = {}

  for artifact in artifacts:
    if os.path.isfile(artifact):
      digest_object = toto.ssl_crypto.hash.digest_filename(artifact)
      artifacts_dict[artifact] = digest_object.hexdigest()

    elif os.path.isdir(artifact):
      for root, dirs, files in os.walk(artifact):
        for name in files:
          filename = os.path.join(root, name)
          digest_object = toto.ssl_crypto.hash.digest_filename(filename)
          artifacts_dict[filename] = digest_object.hexdigest()

  return artifacts_dict


def execute_link(link_cmd_args):
  """Takes a command and its options and arguments of the software supply 
  chain as input, runs the command in a suprocess, records the stdout, 
  stderr and return value of the command and returns them. Stdout and stderr
  are called byproducts."""

  # XXX: Use SpooledTemporaryFile if we expect very large outputs
  stdout_file = tempfile.TemporaryFile()
  stderr_file = tempfile.TemporaryFile()

  return_value = subprocess.call(link_cmd_args,
      stdout=stdout_file, stderr=stderr_file)

  stdout_file.seek(0)
  stderr_file.seek(0)

  stdout_str = stdout_file.read()
  stderr_str = stderr_file.read()

  return {"stdout": stdout_str, "stderr": stderr_str}, return_value


def create_link_metadata(name, materials, products, byproducts,
    ran_command, return_value):
  """Takes the state of the material (before link command execution), the state
  of the product (after link command execution) and the by-products of the link
  command execution and creates the link metadata according to the specified 
  metadata format."""

  link_dict = {
    "name" : name,
    "materials" : materials,
    "products" : products,
    "byproducts" : byproducts,
    "ran_command" : ran_command,
    "return_value" : return_value
  }

  return  toto.models.link.Link.read(link_dict)


def run_link(name, materials, products, toto_cmd_args, key):
  """Performs all actions associated with toto run-link.
  XXX: This should probably be atomic, i.e. all or nothing"""

  # Record - Run - Record
  materials_dict = record_artifacts_as_dict(materials)
  byproducts, return_value = execute_link(toto_cmd_args)
  products_dict = record_artifacts_as_dict(products)

  link = create_link_metadata(name, materials_dict, products_dict, byproducts,
    toto_cmd_args, return_value)

  link.sign(key)
  link.dump()

  