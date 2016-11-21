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
        " install and use the much more recent subprocess32")
    import subprocess
else:
  import subprocess

import toto.models.link
import toto.log as log

import toto.ssl_crypto.hash
import toto.ssl_crypto.formats

def _hash_artifact(filepath, hash_algorithms=['sha256']):
  """Internal helper that takes a filename and hashes the respective file's
  contents using the passed hash_algorithms and returns a hashdict conformant
  with ssl_crypto.formats.HASHDICT_SCHEMA. """
  toto.ssl_crypto.formats.HASHALGORITHMS_SCHEMA.check_match(hash_algorithms)
  hash_dict = {}

  for algorithm in hash_algorithms:
    digest_object = toto.ssl_crypto.hash.digest_filename(filepath, algorithm)
    hash_dict.update({algorithm: digest_object.hexdigest()})

  toto.ssl_crypto.formats.HASHDICT_SCHEMA.check_match(hash_dict)

  return hash_dict


def _normalize_path(path):
  """Internal helper that strips "./" on the left side of the path. """
  if path.startswith("./"):
      return path[2:]
  return path


def record_artifacts_as_dict(artifacts):
  """
  <Purpose>
    Hashes each file in the passed path list. If the path list contains
    paths to directories the directory tree(s) are traversed.

    The files a link command is executed on are called materials.
    The files that result form a link command execution are called
    products.

  <Arguments>
    artifacts:
            A list of file or directory paths used as materials or products for
            the link command.

  <Exceptions>
    TBA (see https://github.com/in-toto/in-toto/issues/6)

  <Side Effects>
    Calls functions to generate cryptographic hashes.

  <Returns>
    A dictionary with file paths as keys and the files' hashes as values.
  """
  artifacts_dict = {}

  if not artifacts:
    return artifacts_dict

  for artifact in artifacts:

    if not os.path.exists(artifact):
      log.warning("path: {} does not exist, skipping..".format(artifact))
      continue 

    if os.path.isfile(artifact):
      artifacts_dict[_normalize_path(artifact)] = _hash_artifact(artifact)
    elif os.path.isdir(artifact):
      for root, dirs, files in os.walk(artifact):
        for name in files:
          filepath = os.path.join(root, name)
          artifacts_dict[_normalize_path(filepath)] = _hash_artifact(filepath)

  return artifacts_dict


def execute_link(link_cmd_args, record_byproducts):
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
    record_byproducts:
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
      Note: If record_byproducts is False, the dict values are empty strings.
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

  if record_byproducts:
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

  return {"stdout": stdout_str, "stderr": stderr_str}, return_value

def create_link_metadata(link_name, materials_dict={}, products_dict={},
    link_cmd_args="", byproducts={}, return_value=None):
  """
  <Purpose>
    Takes the state of the materials (before link command execution), the state
    of the products (after link command execution) and the by-products and
    return value of the link command execution and creates and returns a
    Link metadata object.

  <Arguments>
    link_name:
            A unique name to relate link metadata with a step defined in the
            layout.
    materials_dict: (optional)
            A dictionary with file paths as keys and the files' hashes as
            values.
    products_dict: (optional)
            A dictionary with file paths as keys and the files' hashes as
            values.
    link_cmd_args: (optional)
            A list where the first element is a command and the remaining
            elements are arguments passed to that command.
    byproducts: (optional)
            A dictionary in the format containing standard output and standard
            error of the executed link command, i.e.:
            {"stdout": "<standard output", "stderr": "<standard error>"}
    return_value: (optional)
            The return value of the executed command.

  <Exceptions>
    TBA (see https://github.com/in-toto/in-toto/issues/6)

  <Side Effects>
    Creates a Link object from a Python dictionary.

  <Returns>
    - A Link metadata object
  """
  link_dict = {
    "name" : link_name,
    "materials" : materials_dict,
    "products" : products_dict,
    "command" : link_cmd_args,
    "byproducts" : byproducts,
    "return_value" : return_value
  }
  return  toto.models.link.Link.read(link_dict)


def run_link(link_name, materials_list, products_list, link_cmd_args,
    record_byproducts=False):
  """
  <Purpose>
    Wrapper to record materials, execute a link, record products and create
    and return a Link metadata object.

  <Arguments>
    link_name:
            A unique name to relate link metadata with a step defined in the
            layout.
    materials_list:
            A list of file or directory paths used as materials for
            the link command.
    products_list:
            A list of file or directory paths used as materials for
            the link command.
    link_cmd_args:
            A list where the first element is a command and the remaining
            elements are arguments passed to that command.
    record_byproducts:
            A bool that specifies whether to redirect standard output and
            and standard error to a temporary file which is returned to the
            caller (True) or not (False).

  <Exceptions>
    TBA (see https://github.com/in-toto/in-toto/issues/6)

  <Side Effects>
    - Calls function to record materials.
    - Calls function to execute link command.
    - Calls function to record products.
    - Calls function to create Link object.

  <Returns>
    A Link metadata object
  """
  materials_dict = record_artifacts_as_dict(materials_list)
  byproducts, return_value = execute_link(link_cmd_args, record_byproducts)
  products_dict = record_artifacts_as_dict(products_list)
  return create_link_metadata(link_name, materials_dict, products_dict,
      link_cmd_args, byproducts, return_value)

