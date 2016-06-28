"""
<Program Name>
  verifylib.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  June 28, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provide a library to verify the software supply chains integrity.
  The supply chain is reconstructed using each link's metadata, and checking
  whether the product of a link was used as the material of the subsequent 
  links.
  Furthermore this library checks whether the metadata was signed by an 
  authorized functionary and if the by-products of a link align with the link
  definition in the toto layout file.

"""
import toto.util
import toto.ssl_crypto.keys


def _verify_metadata_signature(key_dict, signature, data):
  """Takes a key dictionary a signature and the data that was signed by the
  signature and return whether the signature is valid for the given data """
  return toto.ssl_crypto.keys.verify_signature(key_dict, signature, data)