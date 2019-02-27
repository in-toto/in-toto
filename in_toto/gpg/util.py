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
import re
import logging

from distutils.version import StrictVersion # pylint: disable=no-name-in-module,import-error

import cryptography.hazmat.backends as backends
import cryptography.hazmat.primitives.hashes as hashing

import in_toto.gpg.exceptions
import in_toto.process
import in_toto.gpg.constants

# Inherits from in_toto base logger (c.f. in_toto.log)
log = logging.getLogger(__name__)

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
  # As per RFC4880 Section 5.2.4., we need to hash the content,
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
            type. See in_toto.gpg.constants.PACKET_TYPE_* for available types.

  <Exceptions>
    in_toto.gpg.exceptions.PacketParsingError
            If the new format packet length encodes a partial body length
            If the old format packet length encodes an indeterminate length
            If header or body length could not be determined
            If the expected_type was passed and does not match the packet type

    IndexError
            If the passed data is incomplete

  <Side Effects>
    None.

  <Returns>
    The RFC4880-compliant packet payload, its length and its type.
    (see RFC 4880 4.3. for the list of available packet types)
  """
  data = bytearray(data)
  header_len = None
  body_len = None

  # If Bit 6 of 1st octet is set we parse a New Format Packet Length, and
  # an Old Format Packet Lengths otherwise
  if data[0] & 0x40: # pragma: no cover
    # In new format packet lengths the packet type is encoded in Bits 5-0 of
    # the 1st octet of the packet
    packet_type = data[0] & 0x3f

    # The rest of the packet header is the body length header, which may
    # consist of one, two or five octets. To disambiguate the RFC, the first
    # octet of the body length header is the second octet of the packet.
    if data[1] < 192:
      header_len = 2
      body_len = data[1]

    elif data[1] >= 192 and data[1] <= 223:
      header_len = 3
      body_len = (data[1] - 192 << 8) + data[2] + 192

    elif data[1] >= 224 and data[1] < 255:
      raise in_toto.gpg.exceptions.PacketParsingError("New length format "
          " packets of partial body lengths are not supported")

    elif data[1] == 255:
      header_len = 6
      body_len = data[2] << 24 | data[3] << 16 | data[4] << 8 | data[5]

    else:
      # raise PacketParsingError below if lengths cannot be determined
      pass

  else:
    # In old format packet lengths the packet type is encoded in Bits 5-2 of
    # the 1st octet and the length type in Bits 1-0
    packet_type = (data[0] & 0x3c ) >> 2
    length_type = data[0] & 0x03

    # The body length is encoded using one, two, or four octets, starting
    # with the second octet of the packet
    if length_type == 0:
      body_len = data[1]
      header_len = 2

    elif length_type == 1: # pragma: no branch
      header_len = 3
      body_len = struct.unpack(">H", data[1:header_len])[0]

    elif length_type == 2: # pragma: no cover
      header_len = 5
      body_len = struct.unpack(">I", data[1:header_len])[0]

    elif length_type == 3: # pragma: no cover
      raise in_toto.gpg.exceptions.PacketParsingError("Old length format "
          "packets of indeterminate length are not supported")

    else: # pragma: no cover
      # raise PacketParsingError below if lengths cannot be determined
      pass

  if header_len == None or body_len == None: # pragma: no cover
    raise in_toto.gpg.exceptions.PacketParsingError("Could not determine "
        "packet length")

  if expected_type != None and packet_type != expected_type: # pragma: no cover
    raise in_toto.gpg.exceptions.PacketParsingError("Expected packet {}, "
        "but got {} instead!".format(expected_type, packet_type))

  return data[header_len:header_len+body_len], header_len+body_len, packet_type


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

    if length >= 192 and length < 255 : # pragma: no cover
      length = ((length - 192 << 8) + (subpacket_octets[ptr] + 192))
      ptr += 1

    if length == 255: # pragma: no cover
      length = struct.unpack(">I", subpacket_octets[ptr:ptr + 4])[0]
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
  command = in_toto.gpg.constants.GPG_VERSION_COMMAND
  process = in_toto.process.run(command, stdout=in_toto.process.PIPE,
    stderr=in_toto.process.PIPE, universal_newlines=True)

  full_version_info = process.stdout
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


def get_hashing_class(hash_algorithm_id):
  """
  <Purpose>
    Return a pyca/cryptography hashing class reference for the passed RFC4880
    hash algorithm ID.

  <Arguments>
    hash_algorithm_id:
            one of SHA1, SHA256, SHA512 (see in_toto.gpg.constants)

  <Exceptions>
    ValueError
            if the passed hash_algorithm_id is not supported.

  <Returns>
    A pyca/cryptography hashing class

  """
  if hash_algorithm_id == in_toto.gpg.constants.SHA1:
    return hashing.SHA1

  elif hash_algorithm_id == in_toto.gpg.constants.SHA256:
    return hashing.SHA256

  elif hash_algorithm_id == in_toto.gpg.constants.SHA512:
    return hashing.SHA512

  else:
    raise ValueError("Hash algorithm '{}' not supported, must be one of '{}' "
        "(see RFC4880 9.4. Hash Algorithms).".format(hash_algorithm_id,
        {in_toto.gpg.constants.SHA1, in_toto.gpg.constants.SHA256,
         in_toto.gpg.constants.SHA512}))
