"""
<Program Name>
  toto-run.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  June 27, 2013 

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provide a command line interface which wraps toto metadata recording
  around any command of the software supply chain.
  Toto run options are separated from the command to be executed by 
  a double dash.

  Example Usage
  ```
  python -m toto.toto-run --material <files> --product <files> -- 
    <command-to-execute> <command-options-and-arguments>
  ```

  The program is wrapped around the following taks (implemented in runlib):
    * Record state of material (files the command is executed on)
    * Execute command
    * Capture stdout/stdin/return value of the executed command
    * Record state of product (files after the command was executed)
    * Create metadata file
    * Sign metadata file


  TODO
    * Material/Product
      For now we specify --material and --product explicitly. Later we can think
      of more sophisticate/secure ways to find out which files are being
    * Missing options:
      - Unique identifier to assign to link definition in layout
      - Key (for now uses a default key)
    * Write metadata to place
      We need to decide on the format


"""

import argparse

import toto.util
import toto.runlib


def main():
  pass


if __name__ == '__main__':
  main()