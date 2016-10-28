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
    - Return link object
        can be used to sign and dump
"""
import sys
import os
import tempfile
import logging


# POSIX users (Linux, BSD, etc.) are strongly encouraged to
# install and use the much more recent subprocess32
if os.name == 'posix' and sys.version_info[0] < 3:
  try:
    import subprocess32 as subprocess
  except Exception, e:
    logging.warning("POSIX users (Linux, BSD, etc.) are strongly encouraged to"
        + " install and use the much more recent subprocess32")
    import subprocess
else:
  import subprocess

# TODO: I think we'll get rid of toto formats because we want to use
# model validators instead for toto schemas, we'll still use
# toto.ssl_crypto.formats though

# import toto.formats

import toto.models.link
import toto.log as log

import toto.ssl_crypto.hash
import toto.ssl_crypto.formats


def record_artifacts_as_dict(artifacts):
  """Takes a list of directories and/or filenames as input and creates a dict
  with filepaths as keys and their files' hashes as values.

  The dirs/files a link command is executed on are called materials.
  The dirs/files that result form a link command execution are called
  products."""

  artifacts_dict = {}

  if not artifacts:
    return artifacts_dict

  def _hash_artifact(filepath, hash_algorithms=['sha256']):
    """Takes a filename and hashes the respective file's contents
    using the passed hash_algorithms. Returns a HASHDICT"""

    toto.ssl_crypto.formats.HASHALGORITHMS_SCHEMA.check_match(hash_algorithms)
    hash_dict = {}

    for algorithm in hash_algorithms:
      digest_object = toto.ssl_crypto.hash.digest_filename(filepath, algorithm)
      hash_dict.update({algorithm: digest_object.hexdigest()})

    toto.ssl_crypto.formats.HASHDICT_SCHEMA.check_match(hash_dict)

    return hash_dict

  def _normalize_path(path):
    """Strips "./" on the left side of the path"""

    if path.startswith("./"):
        return path[2:]
    return path  # or whatever

  for artifact in artifacts:
    if os.path.isfile(artifact):
      artifacts_dict[_normalize_path(artifact)] = _hash_artifact(artifact)
    elif os.path.isdir(artifact):
      for root, dirs, files in os.walk(artifact):
        for name in files:
          filepath = os.path.join(root, name)
          artifacts_dict[_normalize_path(filepath)] = _hash_artifact(filepath)

  return artifacts_dict


def execute_link(link_cmd_args, record_byproducts):
  """Takes a command and its options and arguments of the software supply
  chain as input, runs the command in a subprocess, records stdout,
  stderr and return value of the command and returns them. Stdout and stderr
  are called by-products."""

  # TODO: The first approach only redirects the stdout/stderr to a tempfile
  # but we actually want to duplicate it, ideas
  #  - Using a pipe won't work because processes like vi will complain
  #  - Wrapping stdout/sterr in Python does not work because the suprocess
  #    will only take the fd and then uses it natively
  #  - Reading from /dev/stdout|stderr, /dev/tty is *NIX specific
  # Until we come up with a proper solution we use a flag and let the user
  # decide if s/he wants to see or store stdout/stderr
  # btw: we ignore them in the layout anyway

  if record_byproducts:
    # NOTE: Use SpooledTemporaryFile if we expect very large outputs
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

  return {"stdout": stdout_str, "stderr": stderr_str}, return_value

def create_link_metadata(name, materials, products, byproducts,
    command, return_value):
  """Takes the state of the materials (before link command execution), the state
  of the products (after link command execution) and the by-products of the link
  command execution and creates and returns a Link metadata object """

  link_dict = {
    "name" : name,
    "materials" : materials,
    "products" : products,
    "byproducts" : byproducts,
    "command" : command,
    "return_value" : return_value
  }

  return  toto.models.link.Link.read(link_dict)


def run_link(name, materials, products, toto_cmd_args, record_byproducts=False):
  """Performs all actions associated with toto run-link.
  TODO: This should probably be atomic, i.e. all or nothing"""

  # log.doing("record materials for '%s'" % name)
  materials_dict = record_artifacts_as_dict(materials)

  # log.doing("run command '%s' for '%s'" % (toto_cmd_args, name))
  byproducts, return_value = execute_link(toto_cmd_args, record_byproducts)

  # log.doing("record products for '%s'" % name)
  products_dict = record_artifacts_as_dict(products)

  # log.doing("create metadata for '%s'" % name)
  link = create_link_metadata(name, materials_dict, products_dict, byproducts,
    toto_cmd_args, return_value)

  return link

def toto_run(name, materials, products, key, toto_cmd_args,
    record_byproducts=False):
  """Calls run link signs the resulting link metadata and stores it to a file """

  link = toto.runlib.run_link(name, materials, products, toto_cmd_args,
        record_byproducts)

  # log.doing("sign metadata '%s' with key '%s'" % (name, key))
  link.sign(key)
  # log.doing("store metadata '%s' to disk" % name)
  link.dump()
