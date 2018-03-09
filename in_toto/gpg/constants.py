"""
<Module Name>
  constants.py

<Author>
  Santiago Torres-Arias <santiago@nyu.edu>

<Started>
  Nov 15, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  aggregates all the constant definitions and lookup structures for signature
  handling
"""
import in_toto.gpg.rsa as rsa
import in_toto.gpg.dsa as dsa

GPG_SIGN_COMMAND = "gpg2 --detach-sign --digest-algo SHA256 {keyarg} {homearg}"
GPG_EXPORT_PUBKEY_COMMAND = "gpg2 {homearg} --export {keyid}"
GPG_VERSION_COMMAND = "gpg2 --version"

FULLY_SUPPORTED_MIN_VERSION = "2.1.0"

# The packet header is described in RFC4880 section 4.2, and the respective
# packet types can be found in sections 5.2 (signature packet), 5.5.1.1
# (master pubkey packet) and 5.5.1.2 (sub pubkey packet).
PACKET_TYPES = {
    'signature_packet': 0x02,
    'master_pubkey_packet': 0x06,
    'pub_subkey_packet': 0x0E,
}

# See sections 5.2.3 (signature) and 5.2.2 (public key) of RFC4880
SUPPORTED_SIGNATURE_PACKET_VERSIONS = {0x04}
SUPPORTED_PUBKEY_PACKET_VERSIONS = {0x04}

# See section 5.2.3.1 (signature algorithms) of RFC4880
SUPPORTED_SIGNATURE_ALGORITHMS = {
    0x01: {
      "type":"rsa",
      "method": "pgp+rsa-pkcsv1.5",
      "handler": rsa
    },
    0x11: {
      "type": "dsa",
      "method": "pgp+dsa-fips-180-2",
      "handler": dsa
  }
}

SIGNATURE_HANDLERS = {
    "rsa": rsa,
    "dsa": dsa
}

# The constants for hash algorithms are taken from section 9.4 of RFC4880.
SHA256 = 0x08
SUPPORTED_HASH_ALGORITHMS = {SHA256}

# See section 5.2.1 of RFC4880
SIGNATURE_TYPE_BINARY = 0x00

# See section 5.2.3.1 (Issuer) of RFC4880
PARTIAL_KEYID_SUBPACKET = 0x10

# Subpacket 33 is not part of RFC4880
# see https://archive.cert.uni-stuttgart.de/openpgp/2016/06/msg00004.html
FULL_KEYID_SUBPACKET = 0x21
