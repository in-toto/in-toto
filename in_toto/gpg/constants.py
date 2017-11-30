"""
<Module Name>
  gpg/constants.py

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

PACKET_TYPES = {
    'signature_packet': 0x02,
    'main_pubkey_packet': 0x06,
}

SUPPORTED_SIGNATURE_PACKET_VERSIONS = {0x04}
SUPPORTED_PUBKEY_PACKET_VERSIONS = {0x04}

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

SUPPORTED_HASH_ALGORITHMS = {0x08}
SIGNATURE_TYPE_CANONICAL = 0x00
FULL_KEYID_SUBPACKET = 0x21
PARTIAL_KEYID_SUBPACKET = 0x10
