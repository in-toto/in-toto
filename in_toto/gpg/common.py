"""
<Module Name>
  gpg/common.py

<Author>
  Santiago Torres-Arias <santiago@nyu.edu>

<Started>
  Nov 15, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  signature-algorithm-agnostic frontend for the gpg_* parsing, signing and
  verifying functions. These functions select the appropriate functions for
  each algorithm and call it.
"""
import struct
import binascii

import in_toto.log
from in_toto.gpg.constants import (PACKET_TYPES,
        SUPPORTED_PUBKEY_PACKET_VERSIONS, SIGNATURE_TYPE_CANONICAL,
        SUPPORTED_SIGNATURE_PACKET_VERSIONS, SUPPORTED_SIGNATURE_ALGORITHMS,
        SUPPORTED_HASH_ALGORITHMS, SIGNATURE_HANDLERS, FULL_KEYID_SUBPACKET,
        FULLY_SUPPORTED_MIN_VERSION)

from in_toto.gpg.util import (compute_keyid, parse_packet_header,
    parse_subpackets, get_version)
import in_toto.gpg

def gpg_verify_signature(signature_object, pubkey_info, content):
  handler = SIGNATURE_HANDLERS[pubkey_info['type']]
  return handler.gpg_verify_signature(signature_object, pubkey_info, content)

# XXX this doesn't support armored pubkey packets, so use with care.
# pubkey packets are a little bit more complicated than the signature ones
def parse_pubkey_packet(data):

  if not data:
    raise ValueError("Could not parse empty pubkey packet.")

  data = parse_packet_header(data, PACKET_TYPES['main_pubkey_packet'])

  ptr = 0
  keyinfo = {}
  version_number = data[ptr]
  ptr += 1
  if version_number not in SUPPORTED_PUBKEY_PACKET_VERSIONS:
    raise ValueError("This pubkey packet version is not supported!")

  time_of_creation = struct.unpack(">I", data[ptr:ptr + 4])
  ptr += 4

  algorithm = data[ptr]
  ptr += 1

  if algorithm not in SUPPORTED_SIGNATURE_ALGORITHMS:
    raise ValueError("This signature algorithm is not supported!")
  else:
    keyinfo['type'] = SUPPORTED_SIGNATURE_ALGORITHMS[algorithm]['type']
    keyinfo['method'] = SUPPORTED_SIGNATURE_ALGORITHMS[algorithm]['method']
    handler = SIGNATURE_HANDLERS[keyinfo['type']]

  keyinfo['keyid'] = compute_keyid(data)
  key_params = handler.get_pubkey_params(data[ptr:])

  return key_params, keyinfo

# this takes the signature as created by pgp and turns it into a tuf-like
# representation (to be used with gpg_sign_object)
def parse_signature_packet(data):

  data = parse_packet_header(data, PACKET_TYPES['signature_packet'])
  ptr = 0

  # we get the version number, which we also expect to be v4, or we bail
  # FIXME: support v3 type signatures (which I havent' seen in the wild)
  version_number = data[ptr]
  ptr += 1
  if version_number not in SUPPORTED_SIGNATURE_PACKET_VERSIONS:
    raise ValueError("Only version 4 signature packets are supported")

  # here, we want to make sure the signature type is indeed PKCSV1.5 with RSA
  signature_type = data[ptr]
  ptr += 1
  if signature_type != SIGNATURE_TYPE_CANONICAL:
    raise ValueError("We can only use canonical signatures on in-toto")

  signature_algorithm = data[ptr]
  ptr += 1

  if signature_algorithm not in SUPPORTED_SIGNATURE_ALGORITHMS:
    raise ValueError("This signature algorithm is not supported!")

  key_type = SUPPORTED_SIGNATURE_ALGORITHMS[signature_algorithm]['type']
  handler = SIGNATURE_HANDLERS[key_type]

  hash_algorithm = data[ptr]
  ptr += 1

  if hash_algorithm not in SUPPORTED_HASH_ALGORITHMS:
    raise ValueError("This library only supports sha256 as "
            "the hash algorithm!")

  # obtain the hashed octets.
  hashed_octet_count = struct.unpack(">H", data[ptr:ptr+2])[0]
  ptr += 2
  hashed_subpackets = data[ptr:ptr+hashed_octet_count]
  hashed_subpacket_info = parse_subpackets(hashed_subpackets)

  # check wether we were actually able to read this much hashed octets
  if len(hashed_subpackets) != hashed_octet_count:
    raise ValueError("this signature packet is missing hashed octets!")

  ptr += hashed_octet_count
  other_headers_ptr = ptr

  unhashed_octet_count = struct.unpack(">H", data[ptr: ptr + 2])[0]
  ptr += 2
  unhashed_subpackets = data[ptr:ptr+unhashed_octet_count]
  unhashed_subpacket_info = parse_subpackets(unhashed_subpackets)
  ptr += unhashed_octet_count

  # this is a somewhat convoluted way to compute the keyid from the signature
  # subpackets. Try to obtain the FULL_KEYID_SUBPACKET and bail even if the
  # partial one is available.
  keyid = filter(lambda x: True if x[0] == FULL_KEYID_SUBPACKET else False,
          hashed_subpacket_info)

  if keyid:
    keyid = binascii.hexlify(keyid[0][1][2:])

  else:
    keyid = ""
    in_toto.log.warn("can't parse the full keyid on this signature packet."
        "you need at least gpg version '{}'. Your version is '{}'".format(
        FULLY_SUPPORTED_MIN_VERSION, get_version()))


  left_hash_bits = struct.unpack(">H", data[ptr:ptr+2])[0]
  ptr += 2

  # Notice the /8 at the end, this length is the bitlength, not the length of
  # the data in bytes (as len reports it)
  signature = handler.get_signature_params(data[ptr:])

  return {
    'keyid': "{}".format(keyid),
    'other_headers': binascii.hexlify(data[:other_headers_ptr]).decode('ascii'),
    'signature': binascii.hexlify(signature).decode('ascii')
  }
