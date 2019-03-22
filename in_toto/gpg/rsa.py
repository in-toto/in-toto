"""
<Module Name>
  rsa.py

<Author>
  Santiago Torres-Arias <santiago@nyu.edu>

<Started>
  Nov 15, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  RSA-specific handling routines for signature verification and key parsing
"""
import binascii

import cryptography.hazmat.primitives.asymmetric.rsa as rsa
import cryptography.hazmat.backends as backends
import cryptography.hazmat.primitives.asymmetric.padding as padding
import cryptography.hazmat.primitives.asymmetric.utils as utils
import cryptography.exceptions

import in_toto.gpg.util
import in_toto.gpg.exceptions
import in_toto.gpg.formats


def create_pubkey(pubkey_info):
  """
  <Purpose>
    Create and return an RSAPublicKey object from the passed pubkey_info
    using pyca/cryptography.

  <Arguments>
    pubkey_info:
            The RSA pubkey info dictionary as specified by
            gpg.formats.RSA_PUBKEY_SCHEMA

  <Exceptions>
    securesystemslib.exceptions.FormatError if
      pubkey_info does not match gpg.formats.RSA_PUBKEY_SCHEMA

  <Returns>
    A cryptography.hazmat.primitives.asymmetric.rsa.RSAPublicKey based on the
    passed pubkey_info.

  """
  in_toto.gpg.formats.RSA_PUBKEY_SCHEMA.check_match(pubkey_info)

  e = int(pubkey_info['keyval']['public']['e'], 16)
  n = int(pubkey_info['keyval']['public']['n'], 16)
  pubkey = rsa.RSAPublicNumbers(e, n).public_key(backends.default_backend())

  return pubkey


def get_pubkey_params(data):
  """
  <Purpose>
    Parse the public key parameters as multi-precision-integers.

  <Arguments>
    data:
           the RFC4880-encoded public key parameters data buffer as described
           in the fifth paragraph of section 5.5.2.

  <Exceptions>
    in_toto.gpg.exceptions.PacketParsingError: if the public key parameters are
    malformed

  <Side Effects>
    None.

  <Returns>
    The decoded signature buffer
  """
  ptr = 0

  modulus_length = in_toto.gpg.util.get_mpi_length(data[ptr: ptr + 2])
  ptr += 2
  modulus = data[ptr:ptr + modulus_length]
  if len(modulus) != modulus_length: # pragma: no cover
    raise in_toto.gpg.exceptions.PacketParsingError(
        "This modulus MPI was truncated!")
  ptr += modulus_length

  exponent_e_length = in_toto.gpg.util.get_mpi_length(data[ptr: ptr + 2])
  ptr += 2
  exponent_e = data[ptr:ptr + exponent_e_length]
  if len(exponent_e) != exponent_e_length: # pragma: no cover
    raise in_toto.gpg.exceptions.PacketParsingError(
        "This e MPI has been truncated!")

  return {
    "e": binascii.hexlify(exponent_e).decode('ascii'),
    "n": binascii.hexlify(modulus).decode("ascii"),
  }


def get_signature_params(data):
  """
  <Purpose>
    Parse the signature parameters as multi-precision-integers.

  <Arguments>
    data:
           the RFC4880-encoded public key parameters data buffer as described
           in the third paragraph of section 5.2.2.

  <Exceptions>
    in_toto.gpg.exceptions.PacketParsingError: if the public key parameters are
    malformed

  <Side Effects>
    None.

  <Returns>
    The decoded signature buffer
  """

  ptr = 0
  signature_length = in_toto.gpg.util.get_mpi_length(data[ptr:ptr+2])
  ptr += 2
  signature = data[ptr:ptr + signature_length]
  if len(signature) != signature_length: # pragma: no cover
    raise in_toto.gpg.exceptions.PacketParsingError(
        "This signature was truncated!")

  return signature


def gpg_verify_signature(signature_object, pubkey_info, content,
    hash_algorithm_id):
  """
  <Purpose>
    Verify the passed signature against the passed content with the passed
    RSA public key using pyca/cryptography.

  <Arguments>
    signature_object:
            A signature dictionary as specified by
            gpg.formats.SIGNATURE_SCHEMA

    pubkey_info:
            The RSA public key info dictionary as specified by
            gpg.formats.RSA_PUBKEY_SCHEMA

    content:
            The signed bytes against which the signature is verified

    hash_algorithm_id:
            one of SHA1, SHA256, SHA512 (see in_toto.gpg.constants) used to
            verify the signature
            NOTE: Overrides any hash algorithm specification in "pubkey_info"'s
            "hashes" or "method" fields.

  <Exceptions>
    securesystemslib.exceptions.FormatError if:
      signature_object does not match gpg.formats.SIGNATURE_SCHEMA
      pubkey_info does not match gpg.formats.RSA_PUBKEY_SCHEMA

    ValueError:
      if the passed hash_algorithm_id is not supported (see
      in_toto.gpg.util.get_hashing_class)

  <Returns>
    True if signature verification passes and False otherwise

  """
  in_toto.gpg.formats.SIGNATURE_SCHEMA.check_match(signature_object)
  in_toto.gpg.formats.RSA_PUBKEY_SCHEMA.check_match(pubkey_info)

  hasher = in_toto.gpg.util.get_hashing_class(hash_algorithm_id)

  pubkey_object = create_pubkey(pubkey_info)

  # zero-pad the signature due to a discrepancy between the openssl backend
  # and the gnupg interpretation of PKCSv1.5. Read more at:
  # https://github.com/in-toto/in-toto/issues/171#issuecomment-440039256
  # we are skipping this if on the tests because well, how would one test this
  # deterministically.
  pubkey_length = len(pubkey_info['keyval']['public']['n'])
  signature_length = len(signature_object['signature'])
  if pubkey_length != signature_length: # pragma: no cover
    zero_pad = "0"*(pubkey_length - signature_length)
    signature_object['signature'] = "{}{}".format(zero_pad,
        signature_object['signature'])

  digest = in_toto.gpg.util.hash_object(
      binascii.unhexlify(signature_object['other_headers']),
      hasher(), content)

  try:
    pubkey_object.verify(
      binascii.unhexlify(signature_object['signature']),
      digest,
      padding.PKCS1v15(),
      utils.Prehashed(hasher())
    )
    return True
  except cryptography.exceptions.InvalidSignature:
    return False
