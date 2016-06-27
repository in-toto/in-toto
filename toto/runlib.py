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

# XXX LP: POSIX users (Linux, BSD, etc.) are strongly encouraged to 
# install and use the much more recent subprocess32
if os.name == 'posix' and sys.version_info[0] < 3:
    import subprocess32 as subprocess
else:
    import subprocess


def record_link_state(link_files):
  """ Takes a directory or file names as input and creates a hash. 
  The dir/files a link command is executed on are called material. The dir/files
  the result form a link command execution are called product. """
  pass

def execute_link(link_cmd_args):
  """ Takes a command and its options and arguments of the software supply 
  chain as input, runs the command in a suprocess, records the stdout and 
  stderr and return value of the command and returns them. Stdout, stderr and 
  return value are called by_products. """
  pass

def create_link_metadata(material_state, product_state, by_products):
  """ Takes the state of the material (before link command execution), the state
  of the product (after link command execution) and the by-products of the link
  command execution and creates the link metadata according to the specified 
  metadata format. """
  pass

def sign_link_metadata(link_metdata, functionary_key):
  """ Takes a link metadata and the key of the functionary who executed the 
  according link command and signs the metadata. """
  pass


def run_link(material, toto_cmd_args, product):
  pass
  