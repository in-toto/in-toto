"""
<Module Name>
  common.py

<Author>
  Santiago Torres-Arias <santiago@nyu.edu>

<Started>
  Nov 15, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides algorithm-agnostic gpg public key and signature parsing functions.
  The functions select the appropriate functions for each algorithm and
  call them.

"""
import struct
import binascii
import logging

import in_toto.gpg.util
from in_toto.gpg.constants import (PACKET_TYPES,
        SUPPORTED_PUBKEY_PACKET_VERSIONS, SIGNATURE_TYPE_BINARY,
        SUPPORTED_SIGNATURE_PACKET_VERSIONS, SUPPORTED_SIGNATURE_ALGORITHMS,
        SUPPORTED_HASH_ALGORITHMS, SIGNATURE_HANDLERS, FULL_KEYID_SUBPACKET,
        FULLY_SUPPORTED_MIN_VERSION)


# Inherits from in_toto base logger (c.f. in_toto.log)
log = logging.getLogger(__name__)


def parse_pubkey_packet(data):
  """
  <Purpose>
    Parse the public key information on an RFC4880-encoded public-key data
    buffer

  <Arguments>
    data:
          the RFC4880-encoded public-key data buffer as described in section
          5.4 (and 5.5.1.1).

          WARNING: this doesn't support armored pubkey packets, so use with
          care. pubkey packets are a little bit more complicated than the
          signature ones

  <Exceptions>
    ValueError: if the public key packet is not supported or the data is
      malformed

  <Side Effects>
    None.

  <Returns>
    a tuple containing the key information and its payload.
  """

  if not data:
    raise ValueError("Could not parse empty pubkey packet.")

  data = in_toto.gpg.util.parse_packet_header(
      data, PACKET_TYPES['main_pubkey_packet'])

  ptr = 0
  keyinfo = {}
  version_number = data[ptr]
  ptr += 1
  if version_number not in SUPPORTED_PUBKEY_PACKET_VERSIONS: # pragma: no cover
    raise ValueError("This pubkey packet version is not supported!")

  # NOTE: Uncomment this line to decode the time of creation
  # time_of_creation = struct.unpack(">I", data[ptr:ptr + 4])
  ptr += 4

  algorithm = data[ptr]
  ptr += 1

  if algorithm not in SUPPORTED_SIGNATURE_ALGORITHMS: # pragma: no cover
    raise ValueError("This signature algorithm is not supported. Please"
        " verify that this gpg key is used for creating either DSA or RSA"
        " signatures.")
  else:
    keyinfo['type'] = SUPPORTED_SIGNATURE_ALGORITHMS[algorithm]['type']
    keyinfo['method'] = SUPPORTED_SIGNATURE_ALGORITHMS[algorithm]['method']
    handler = SIGNATURE_HANDLERS[keyinfo['type']]

  keyinfo['keyid'] = in_toto.gpg.util.compute_keyid(data)
  key_params = handler.get_pubkey_params(data[ptr:])

  return key_params, keyinfo


def parse_signature_packet(data):
  """
  <Purpose>
    Parse the signature information on an RFC4880-encoded binary signature data
    buffer

  <Arguments>
    data:
           the RFC4880-encoded binary signature data buffer as described in
           section 5.2 (and 5.2.3.1).

  <Exceptions>
    ValueError: if the signature packet is not supported or the data is
      malformed

  <Side Effects>
    None.

  <Returns>
    The decoded signature buffer
  """

  data = in_toto.gpg.util.parse_packet_header(
      data, PACKET_TYPES['signature_packet'])

  ptr = 0

  # we get the version number, which we also expect to be v4, or we bail
  # FIXME: support v3 type signatures (which I haven't seen in the wild)
  version_number = data[ptr]
  ptr += 1
  if version_number not in SUPPORTED_SIGNATURE_PACKET_VERSIONS: # pragma: no cover
    raise ValueError("Only version 4 gpg signatures are supported.")

  # here, we want to make sure the signature type is indeed PKCSV1.5 with RSA
  signature_type = data[ptr]
  ptr += 1

  # INFO: as per RFC4880 (section 5.2.1) there are multiple types of signatures
  # with different purposes (e.g., there is one for pubkey signatures, key
  # revocation, etc.). Binary document signatures are the ones done over
  # "arbitrary text," and it's the one it's defaulted to when doing a signature
  # (i.e., gpg --sign [...])
  if signature_type != SIGNATURE_TYPE_BINARY: # pragma: no cover
    raise ValueError("We can only use binary signature types (i.e., "
        "gpg --sign [...] or signatures created by in-toto).")

  signature_algorithm = data[ptr]
  ptr += 1

  if signature_algorithm not in SUPPORTED_SIGNATURE_ALGORITHMS: # pragma: no cover
    raise ValueError("This signature algorithm is not supported. please"
        " verify that your gpg configuration is creating either DSA or RSA"
        " signatures")

  key_type = SUPPORTED_SIGNATURE_ALGORITHMS[signature_algorithm]['type']
  handler = SIGNATURE_HANDLERS[key_type]

  hash_algorithm = data[ptr]
  ptr += 1

  if hash_algorithm not in SUPPORTED_HASH_ALGORITHMS: # pragma: no cover
    raise ValueError("This library only supports SHA256 as "
        "the hash algorithm!")

  # Obtain the hashed octets
  hashed_octet_count = struct.unpack(">H", data[ptr:ptr+2])[0]
  ptr += 2
  hashed_subpackets = data[ptr:ptr+hashed_octet_count]
  hashed_subpacket_info = in_toto.gpg.util.parse_subpackets(hashed_subpackets)

  # Check whether we were actually able to read this much hashed octets
  if len(hashed_subpackets) != hashed_octet_count: # pragma: no cover
    raise ValueError("This signature packet seems to be corrupted."
        "It is missing hashed octets!")

  ptr += hashed_octet_count
  other_headers_ptr = ptr

  unhashed_octet_count = struct.unpack(">H", data[ptr: ptr + 2])[0]
  ptr += 2
  # NOTE: Uncomment this part to get the information from the
  # unhashed subpackets. They'll be commented as they are unused
  # right now
  # unhashed_subpackets = data[ptr:ptr+unhashed_octet_count]
  # unhashed_subpacket_info = in_toto.gpg.util.parse_subpackets(
  #     unhashed_subpackets)
  ptr += unhashed_octet_count

  # This is a somewhat convoluted way to compute the keyid from the signature
  # subpackets. Try to obtain the FULL_KEYID_SUBPACKET and bail even if the
  # partial one is available.
  keyid = []
  for subpacket_tuple in hashed_subpacket_info:
    if subpacket_tuple[0] == FULL_KEYID_SUBPACKET: # pragma: no cover
      keyid.append(subpacket_tuple)

  # Excluded so that coverage does not vary in different test environments
  if keyid: # pragma: no cover
    keyid = binascii.hexlify(keyid[0][1][2:]).decode("ascii")

  else: # pragma: no cover
    keyid = ""
    log.warning("Can't parse the full keyid on this signature packet."
        "You need at least gpg version '{}'. Your version is '{}'.".format(
        FULLY_SUPPORTED_MIN_VERSION, in_toto.gpg.util.get_version()))

  # Uncomment this variable to obtain the left-hash-bits information (used for
  # early rejection)
  #left_hash_bits = struct.unpack(">H", data[ptr:ptr+2])[0]
  ptr += 2

  signature = handler.get_signature_params(data[ptr:])

  return {
    'keyid': "{}".format(keyid),
    'other_headers': binascii.hexlify(data[:other_headers_ptr]).decode('ascii'),
    'signature': binascii.hexlify(signature).decode('ascii')
  }
