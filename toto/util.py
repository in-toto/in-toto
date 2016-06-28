"""
    TODO: markup
"""

import os
import sys
import pickle

import toto.ssl_crypto.keys

def get_key():
  """Quick throw-away function that returns a test-key from the test-repo. 
  If there is no such key in the test-repo, create one."""

  key_dict_fn = "test-repo/test-key.keydict"

  if os.path.isfile(key_dict_fn):
    with open(key_dict_fn, "r") as key_dict_file:
      key_dict = pickle.loads(key_dict_file.read())

  else:
      key_dict = toto.ssl_crypto.keys.generate_rsa_key()
      with open(key_dict_fn, "w+") as key_dict_file:
        key_dict_file.write(pickle.dumps(key_dict))

  return key_dict