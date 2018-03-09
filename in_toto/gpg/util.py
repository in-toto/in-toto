"""
<Module Name>
  util.py

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

from distutils.version import StrictVersion # pylint: disable=no-name-in-module,import-error

import cryptography.hazmat.backends as backends
import cryptography.hazmat.primitives.hashes as hashing

import in_toto.gpg.exceptions


def get_mpi_length(data):
  """
  <Purpose>
    parses an MPI (Multi-Precision Integer) buffer and returns the appropriate
    length. This is mostly done to perform bitwise to byte-wise conversion.

  <Arguments>
    data: The MPI data

  <Exceptions>
    None

  <Side Effects>
    None

  <Returns>
    The length of the MPI contained at the beginning of this data buffer.
  """
  bitlength = int(struct.unpack(">H", data)[0])
  # Notice the /8 at the end, this length is the bitlength, not the length of
  # the data in bytes (as len reports it)
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


def parse_packet_header(data, expected_type=None):
  """
  <Purpose>
    Parse an RFC4880 packet header and return its payload, length and type.

  <Arguments>
    data:
            An RFC4880 packet as described in section 4.2 of the rfc.

    expected_type: (optional)
            Used to error out if the packet does not have the expected
            type. See in_toto.gpg.constants.PACKET_TYPES for available types.

  <Exceptions>
    in_toto.gpg.exceptions.PacketParsingError
            If the expected_type was passed and does not match the packet type

  <Side Effects>
    None.

  <Returns>
    The RFC4880-compliant packet payload, its length and its type.
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

  if expected_type != None and packet_type != expected_type: # pragma: no cover
    raise in_toto.gpg.exceptions.PacketParsingError("Expected packet {}, "
        "but got {} instead!".format(expected_type, packet_type))

  return data[ptr:ptr+packet_length], ptr+packet_length, packet_type


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
  return binascii.hexlify(hasher.finalize()).decode("ascii")


def parse_subpackets(subpacket_octets):
  """
  <Purpose>
    parse the subpackets fields

  <Arguments>
    subpacket_octets: the unparsed subpacketoctets

  <Exceptions>
    in_toto.gpg.exceptions.PacketParsingError if the octets are malformed

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

  # As per section 5.2.3.1, paragraph four of RFC4880, the subpacket length
  # can be encoded in 1, 2 or 5 octets. Depending on the values described here
  # we unpack 1, 2 or 5 octets to decode the length.
  # The subpacket length includes packet type (first octet) and payload, but
  # not the length of the length.
  while ptr < len(subpacket_octets):
    length = subpacket_octets[ptr]
    ptr += 1

    if length > 192 and length < 255 : # pragma: no cover
      length = ((length - 192 << 8) + (subpacket_octets[ptr] + 192))
      ptr += 1

    if length == 255: # pragma: no cover
      length = struct.unpack(">I", subpacket_octets[ptr:ptr + 4])
      ptr += 4

    packet_type = subpacket_octets[ptr]
    ptr += 1

    packet_payload = subpacket_octets[ptr:ptr + length - 1]
    parsed_subpackets.append((packet_type, packet_payload))
    ptr += length - 1

  return parsed_subpackets


def get_version():
  """
  <Purpose>
    Uses `gpg2 --version` to get the version info of the installed gpg2
    and extracts and returns the version number.

    The executed base command is defined in constants.GPG_VERSION_COMMAND.

  <Returns>
    Version number string, e.g. "2.1.22"

  """
  command = shlex.split(in_toto.gpg.constants.GPG_VERSION_COMMAND)
  process = subprocess.Popen(command, stdout=subprocess.PIPE,
      universal_newlines=True)
  full_version_info, junk = process.communicate()

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
  # Excluded so that coverage does not vary in different test environments
  if (StrictVersion(installed_version) >=
      StrictVersion(in_toto.gpg.constants.FULLY_SUPPORTED_MIN_VERSION)): # pragma: no cover
    return True

  else: # pragma: no cover
    return False
