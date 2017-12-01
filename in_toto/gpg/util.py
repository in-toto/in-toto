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
import subprocess
import shlex
import re
from distutils.version import StrictVersion

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

def parse_subpackets(subpacket_octets):
  """
  <Purpose>
    parse the subpackets fields

  <Arguments>
    subpacket_octets: the unparsed subpacketoctets

  <Exceptions>
    in_toto.gpg.PacketParsingError if the octets are malformed

  <Side Effects>
    None

  <Returns>
    A list of tuples with like:
        [ (packet_type, data),
          (packet_type, data),
          ...
        ]
  """
  parsed_subpackets = []
  ptr = 0
  while ptr < len(subpacket_octets):
    length = subpacket_octets[ptr]
    ptr += 1
    if length > 192 and length < 255 :
      length = ((length - 192 << 8) + (subpacket_octets[ptr] + 102))
    if length == 255:
      length = 0
      length = struct.unpack(">I", subpacket_octets[ptr: ptr+4])
      ptr += 4

    packet_type = subpacket_octets[ptr]
    packet_payload = subpacket_octets[ptr:ptr + length]
    parsed_subpackets.append((packet_type, packet_payload))
    ptr += length

  return parsed_subpackets

def get_version():
  """
  <Purpose>
    Uses `gpg2 --version` to get the version info of the installed gpg2
    and extracts and returns the version number.

  <Returns>
    Version number string, e.g. "2.1.22"

  """
  command = shlex.split(in_toto.gpg.constants.GPG_VERSION_COMMAND)
  process = subprocess.Popen(command, stdout=subprocess.PIPE)
  full_version_info, _ = process.communicate()

  version_string = re.search(r'(\d\.\d\.\d+)', full_version_info).group(1)

  return version_string


def is_version_fully_supported():
  """
  <Purpose>
    Compares the version of installed gpg2 with the minimal fully supported
    gpg2 version (2.1.0).

  <Returns>
    True if the version returned by `get_version` is greater-equal
    constants.FULLY_SUPPORTED_MIN_VERSION, False otherwise.

  """

  installed_version = get_version()
  if (StrictVersion(installed_version) >=
      StrictVersion(in_toto.gpg.constants.FULLY_SUPPORTED_MIN_VERSION)):
    return True

  else:
    return False
