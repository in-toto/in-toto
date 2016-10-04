"""
    TODO: markup
"""
import os
import sys
import pickle
import json

import toto.ssl_crypto.keys

def create_and_persist_or_load_key(filename):
  """Throw-away function that loads a key file or creates and
  stores it if it does not expist."""

  if not os.path.isfile(filename):
    key_dict = toto.ssl_crypto.keys.generate_rsa_key()
    with open(filename, "w+") as fp:
      key_data = toto.ssl_crypto.keys.format_keyval_to_metadata(
          key_dict["keytype"], key_dict["keyval"], private=True)
      fp.write(json.dumps(key_data))
      return key_dict
  else:
    with open(filename, "r") as fp:
      return toto.ssl_crypto.keys.format_metadata_to_key(json.load(fp))
