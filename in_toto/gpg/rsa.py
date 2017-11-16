"""
<Module Name>
  gpg/rsa.py

<Author>
  Santiago Torres-Arias <santiago@nyu.edu>

<Started>
  Nov 15, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  RSA-specific handling routines for signature verfication and key parsing
"""
import binascii

import cryptography.hazmat.primitives.hashes as hashing
import cryptography.hazmat.primitives.asymmetric.rsa as rsa
import cryptography.hazmat.backends as backends
import cryptography.hazmat.primitives.asymmetric.padding as padding
import cryptography.hazmat.primitives.asymmetric.utils as utils 

from in_toto.gpg.util import get_mpi_length, hash_object

def create_key(pubkey_info):
  e = int(pubkey_info['keyval']['public']['e'], 16)
  n = int(pubkey_info['keyval']['public']['n'], 16)
  pubkey = rsa.RSAPublicNumbers(e, n).public_key(backends.default_backend())
  
  return pubkey

def get_pubkey_params(data):
  ptr = 0

  modulus_length = get_mpi_length(data[ptr: ptr + 2])
  ptr += 2
  modulus = data[ptr:ptr + modulus_length]
  if len(modulus) != modulus_length:
    raise Exception("This modulus MPI was truncated!")
  ptr += modulus_length

  exponent_e_length = get_mpi_length(data[ptr: ptr + 2])
  ptr += 2
  exponent_e = data[ptr:ptr + exponent_e_length]
  if len(exponent_e) != exponent_e_length:
    raise Exception("This e MPI has been truncated!")

  return {
    "e": binascii.hexlify(exponent_e).decode('ascii'),
    "n": binascii.hexlify(modulus).decode("ascii"),
  }

def get_signature_params(data):
  ptr = 0
  signature_length = get_mpi_length(data[ptr:ptr+2])
  ptr += 2
  signature = data[ptr:ptr + signature_length]
  if len(signature) != signature_length:
    raise Exception("This signature was truncated!")

  return signature

def gpg_verify_signature(signature_object, pubkey_info, content):

  pubkey_object = create_key(pubkey_info)

  digest = hash_object(binascii.unhexlify(signature_object['other-headers']),
      hashing.SHA256(), content)

  try:
    pubkey_object.verify(
      binascii.unhexlify(signature_object['signature']),
      digest,
      padding.PKCS1v15(),
      utils.Prehashed(hashing.SHA256())
    )
    return True
  except:
    return False
