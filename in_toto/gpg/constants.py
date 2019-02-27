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
import logging

import in_toto.gpg.rsa as rsa
import in_toto.gpg.dsa as dsa

import in_toto.process as process

# Inherits from in_toto base logger (c.f. in_toto.log)
log = logging.getLogger(__name__)

# By default, we assume and test that gpg2 exists. Otherwise, we assume gpg
# exists.
GPG_COMMAND = "gpg2"
GPG_VERSION_COMMAND = GPG_COMMAND + " --version"

FULLY_SUPPORTED_MIN_VERSION = "2.1.0"

try:
  proc = process.run(GPG_VERSION_COMMAND, stdout=process.PIPE,
    stderr=process.PIPE)

except OSError: # pragma: no cover
  GPG_COMMAND = "gpg"
  GPG_VERSION_COMMAND = GPG_COMMAND + " --version"

GPG_SIGN_COMMAND = GPG_COMMAND + \
                   " --detach-sign --digest-algo SHA256 {keyarg} {homearg}"
GPG_EXPORT_PUBKEY_COMMAND = GPG_COMMAND + " {homearg} --export {keyid}"

# See RFC4880 section 4.3. Packet Tags for a list of all packet types The
# relevant packets defined below are described in sections 5.2 (signature),
# 5.5.1.1 (primary pubkey) and 5.5.1.2 (pub subkey), 5.12 (user id) and 5.13
# (user attribute)
PACKET_TYPE_SIGNATURE = 0x02
PACKET_TYPE_PRIMARY_KEY = 0x06
PACKET_TYPE_USER_ID = 0x0D
PACKET_TYPE_USER_ATTR = 0x11
PACKET_TYPE_SUB_KEY = 0x0E


# See sections 5.2.3 (signature) and 5.5.2 (public key) of RFC4880
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
SHA1 = 0x02
SHA256 = 0x08
SHA512 = 0x0A

# See section 5.2.1 of RFC4880
SIGNATURE_TYPE_BINARY = 0x00
SIGNATURE_TYPE_SUB_KEY_BINDING = 0x18
SIGNATURE_TYPE_CERTIFICATES = {0x10, 0x11, 0x12, 0x13}

# See section 5.2.3.5. (Issuer) of RFC4880
PARTIAL_KEYID_SUBPACKET = 0x10
# See section 5.2.3.28. (Issuer Fingerprint) of rfc4880bis-06
FULL_KEYID_SUBPACKET = 0x21
