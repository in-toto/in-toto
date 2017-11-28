"""
<Module Name>
  gpg/util.py

<Author>
  Santiago Torres-Arias <santiago@nyu.edu>

<Started>
  Nov 15, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  general-purpose utilities for binary data handling and pgp data parsing
"""
import struct
import binascii

import cryptography.hazmat.backends as backends
import cryptography.hazmat.primitives.hashes as hashing
import in_toto.gpg

def get_mpi_length(data):
  """
  <Purpose>
    parses an MPI (Multi-Precision Integer) buffer and returns the appropriate
    length. This is mostly done to perform bitwise to byte-wise conversion.

  <Arguments>
    data: The MPI data

  <Exceptions>
    in-toto.gpg.TruncatedMPIException: if the data provided is not long enough
    to contain this MPI.

  <Side Effects>
    None

  <Returns>
    The length of the MPI contained at the beginning of this data buffer.
  """
  bitlength = int(struct.unpack(">H", data)[0])
  return int((bitlength - 1)/8) + 1

def hash_object(headers, algorithm, content):
  """
  <Purpose>
    Hash data prior to signature verification in conformance of the RFC4880
    openPGP standard.

  <Arguments>
    headers: the additional OpenPGP headers as populated from
    gpg_generate_signature

    algorithm: The hash algorithm object defined by the cryptography.io hashes
    module

    content: the signed content

  <Exceptions>
    None

  <Side Effects>
    None

  <Returns>
    The RFC4880-compliant hashed buffer
  """
  # as per RFC4880 Section 5.2.2 paragraph 4, we need to hash the content,
  # signature headers and add a very opinionated trailing header
  hasher = hashing.Hash(algorithm, backend=backends.default_backend())
  hasher.update(content)
  hasher.update(headers)
  hasher.update(b'\x04\xff')
  hasher.update(struct.pack(">I", len(headers)))

  return hasher.finalize()

def parse_packet_header(data, expected_type):
  """
  <Purpose>
    Parse an RFC4880 packet header and return its payload

  <Arguments>
    data: the packet header buffer

    expected_type: The type of packet expected, as described in section 5.2.3.1
        of RFC4880.

  <Exceptions>
    None

  <Side Effects>
    None

  <Returns>
    The RFC4880-compliant hashed buffer
  """
  data = bytearray(data)
  packet_type = (data[0] & 0x3c ) >> 2
  packet_length_bytes = data[0] & 0x03

  ptr = 3
  if packet_length_bytes == 1:
    packet_length = struct.unpack(">H", data[1:ptr])[0]
  else:
    packet_length = data[1]
    ptr = 2

  if packet_type != expected_type:
    raise in_toto.gpg.PacketParsingError("Expected packet {}, "
        "but got {} instead!".format(expected_type, packet_type))

  return data[ptr:ptr+packet_length]


def compute_keyid(pubkey_packet_data):
  """
  <Purpose>
    compute a keyid from an RFC4880 public-key buffer

  <Arguments>
    pubkey_packet_data: the public-key packet buffer

  <Exceptions>
    None

  <Side Effects>
    None

  <Returns>
    The RFC4880-compliant hashed buffer
  """
  hasher = hashing.Hash(hashing.SHA1(), backend=backends.default_backend())
  hasher.update(b'\x99')
  hasher.update(struct.pack(">H", len(pubkey_packet_data)))
  hasher.update(bytes(pubkey_packet_data))
  return binascii.hexlify(hasher.finalize())
