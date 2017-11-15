#!/usr/bin/env python
import struct
import binascii
import subprocess
import shlex

import cryptography.hazmat.primitives.asymmetric.rsa as rsa
import cryptography.hazmat.backends as backends
import cryptography.hazmat.primitives.asymmetric.padding as padding
import cryptography.hazmat.primitives.hashes as hashing 
import cryptography.hazmat.primitives.asymmetric.utils as rsautils

GPG_SIGN_COMMAND = "gpg --detach-sign {keyarg}"
GPG_EXPORT_PUBKEY_COMMAND = "gpg --export {keyid}"

PACKET_TYPES = {
        'signature_packet': 0x02,
        'main_pubkey_packet': 0x06,
        }
SUPPORTED_SIGNATURE_PACKET_VERSIONS = {0x04}
SUPPORTED_PUBKEY_PACKET_VERSIONS = {0x04}
SUPPORTED_SIGNATURE_ALGORITHMS = {0x01}
SUPPORTED_HASH_ALGORITHMS = {0x08}

SIGNATURE_TYPE_CANONICAL = 0x00

def gpg_verify_signature(signature_object, pubkey, content):

    e = int(pubkey['keyval']['public']['e'], 16)
    n = int(pubkey['keyval']['public']['n'], 16)
    pubkey = rsa.RSAPublicNumbers(e, n).public_key(backends.default_backend())

    # we need to manually hash stuff now 
    hasher = hashing.Hash(hashing.SHA256(), backend=backends.default_backend())

    hasher.update(content)

    # as per RFC4880, we need to hash the signature headers and add a very opinionated
    # trailing header
    hash_headers = binascii.unhexlify(signature['other-headers'])
    hasher.update(hash_headers)
    hasher.update(b'\x04\xff')
    hasher.update(struct.pack(">I", len(hash_headers)))

    digest = hasher.finalize()

    # we need to manually make things work now 
    try:
        pubkey.verify(
            binascii.unhexlify(signature['signature']),
            digest,
            padding.PKCS1v15(),
            rsautils.Prehashed(hashing.SHA256())
        )
        return True
    except:
        return False

# if None is used, then the keyid is not passed down and the signature is
# performed with the default keyid
def gpg_sign_object(content, keyid = None):

    keyarg = ""
    if keyid:
        keyarg="--default-key {}".format(keyid)

    command = GPG_SIGN_COMMAND.format(keyarg=keyarg)
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE,
            stdin=subprocess.PIPE, stderr=None)
    signature_data, _ = process.communicate(content)

    signature = _parse_signature_packet(signature_data)

    return signature

def gpg_export_pubkey(keyid):

    if keyid is None:
        # FIXME: probably needs smarter parsing of what a valid keyid is so as to not
        # export more than on pubkey packet.
        raise Exception("we need to export an individual keyid. Please provide one")

    command = GPG_EXPORT_PUBKEY_COMMAND.format(keyid=keyid)
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE,
            stdin=subprocess.PIPE, stderr=None)
    key_packet, _ = process.communicate()
    
    # FIXME: incredibly-opinionated decision WARNING. We will export the signing subkey only
    # why? because that's the one we need to verify. We will discard all the other pubkey
    # information
    pubkey, keyid = _parse_pubkey_packet(key_packet)

    return {
        "method": "pgp+rsa-pkcsv1.5",
        "type": "rsa",
        "hashes": ["pgp+SHA1"],
        "keyid": keyid,
        "keyval" : {
            "private": "",
            "public": pubkey
            }
        }

# XXX this doesn't support armored pubkey packets, so use with care.
# pubkey packets are a little bit more complicated than the signature ones
def _parse_pubkey_packet(data):

    data = bytearray(data)
    packet_type = (data[0] & 0x3c ) >> 2
    packet_length = data[0] & 0x03

    # we initialize a "data pointer" because things will move around depending
    # on the header packet (that we will read right away)
    ptr = 3
    if packet_length == 1:
        signature_length= struct.unpack(">H", data[1:ptr])[0]
    else:
        signature_length = data[1]
        ptr = 2

    # note, from RFC 4880: "By convention, the top-level key provides signature
    # services, and the subkeys provide encryption services."
    if packet_type != 6:
        raise Excption("This packet is not a main pubkey!")

    version_number = data[ptr]
    ptr += 1
    if version_number not in SUPPORTED_PUBKEY_PACKET_VERSIONS:
        raise Exception("life is bad and I don't support this pubkey packet")

    time_of_creation = struct.unpack(">I", data[ptr:ptr + 4])
    ptr += 4

    algorithm = data[ptr]
    ptr += 1

    modulus_length = _get_mpi_length(data[ptr: ptr + 2])
    ptr += 2
    modulus = data[ptr:ptr + modulus_length]
    if len(modulus) != modulus_length:
        raise Exception("This modulus MPI was truncated!")
    ptr += modulus_length 

    exponent_e_length = _get_mpi_length(data[ptr: ptr + 2])
    ptr += 2
    exponent_e = data[ptr:ptr + exponent_e_length]
    if len(exponent_e) != exponent_e_length:
        raise Exception("This e MPI has been truncated!")

    # lol this feels like javascript
    keyid = _compute_keyid(data[1:ptr + exponent_e_length])

    return {
        "e": binascii.hexlify(exponent_e).decode('ascii'),
        "n": binascii.hexlify(modulus).decode("ascii"),
        }, keyid

def _compute_keyid(pubkey_packet_data):

    hasher = hashing.Hash(hashing.SHA1(), backend=backends.default_backend())
    hasher.update(b'\x99')
    hasher.update(bytes(pubkey_packet_data))
    return binascii.hexlify(hasher.finalize())


# this takes the signature as created by pgp and turns it into a tuf-like
# representation (to be used with gpg_sign_object)
def _parse_signature_packet(data):

    # grab the header information first.
    data = bytearray(data)
    packet_type = (data[0] & 0x3c ) >> 2
    packet_length = data[0] & 0x03

    # we initialize a "data pointer" because things will move around depending
    # on the header packet (that we will read right away)
    other_headers_ptr = 0
    ptr = 3
    if packet_length == 1:
        signature_length = struct.unpack(">H", data[1:ptr])[0]
    else:
        signature_length = data[1]
        ptr = 2

    # we get the version number, which we also expect to be v4, or we bail
    # FIXME: support v4 type signatures (which I havent' seen in the wild)
    version_number = data[ptr]
    ptr += 1
    if version_number not in SUPPORTED_SIGNATURE_PACKET_VERSIONS:
        raise Exception("Only version 4 packets are supported")

    # here, we want to make sure the signature type is indeed PKCSV1.5 with RSA
    signature_type = data[ptr]
    ptr += 1
    if signature_type != SIGNATURE_TYPE_CANONICAL:
        raise Exception("We can only use canonical signatures on in-toto")

    signature_algorithm = data[ptr]
    ptr += 1

    hash_algorithm = data[ptr]
    ptr += 1

    if signature_algorithm not in SUPPORTED_SIGNATURE_ALGORITHMS:
        raise Exception("This library only supports RSA algorithms for now")

    if hash_algorithm not in SUPPORTED_HASH_ALGORITHMS:
        raise Exception("This library only supports sha256 as the hash algorithm!")

    # obtain the hased octets.
    hashed_octet_count = struct.unpack(">H", data[ptr:ptr+2])[0]
    ptr += 2
    hashed_subpackets = data[ptr:ptr+hashed_octet_count]
    # check wether we were actually able to read this much hashed octets
    if len(hashed_subpackets) != hashed_octet_count:
        raise Exception("this signature packet is missing hashed octets!")
    ptr += hashed_octet_count
    other_headers_ptr = ptr

    # we don't need this, but we will still parse them for the sake of 
    # getting a keyid, this should be smarter down the line
    # FIXME
    unhashed_octet_count = struct.unpack(">H", data[ptr: ptr + 2])[0]
    ptr += 2

    unhashed_subpackets = data[ptr:ptr+unhashed_octet_count]
    ptr += unhashed_octet_count

    left_hash_bits = struct.unpack(">H", data[ptr:ptr+2])[0]
    ptr += 2

    # Notice the /8 at the end, this length is the bitlength, not the length of
    # the data in bytes (as len reports it)
    signature_length = _get_mpi_length(data[ptr:ptr+2])
    ptr += 2
    signature = data[ptr:ptr + signature_length]
    if len(signature) != signature_length:
        raise Exception("This signature was truncated!")

    return {
        'keyid': "0x{}".format(binascii.hexlify(unhashed_subpackets).decode('ascii')),
        'other-headers': binascii.hexlify(data[3:other_headers_ptr]).decode('ascii'),
        'signature': binascii.hexlify(signature).decode('ascii')
    }

def _get_mpi_length(data):
    bitlength = int(struct.unpack(">H", data)[0])

    # ghetto ceil because ceil is the devil
    return int((bitlength - 1)/8) + 1

if __name__ == "__main__":
    data = b'ayylmao\n'
    signature = gpg_sign_object(data)
    print(signature)

    pubkey = gpg_export_pubkey("903BAB73640EB6D65533EFF3468F122CE8162295")
    print(pubkey)
    if gpg_verify_signature(signature, pubkey, data):
        print("verification test works!")
    if not gpg_verify_signature(signature, pubkey, b'ayynotlmao'):
        print("failing with fake data worked!")
