"""
<Module Name>
  gpg/functions.py

<Author>
  Santiago Torres-Arias <santiago@nyu.edu>

<Started>
  Nov 15, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  publicly-usable functions for exporting public-keys, signing data and
  verifying signatures.
"""
import subprocess
import shlex

from in_toto.gpg.constants import GPG_EXPORT_PUBKEY_COMMAND, GPG_SIGN_COMMAND
from in_toto.gpg.common import (parse_signature_packet, parse_pubkey_packet,
    gpg_verify_signature)

# if None is used, then the keyid is not passed down and the signature is
# performed with the default keyid
def gpg_sign_object(content, keyid = None, homedir = None):

  keyarg = ""
  if keyid:
    keyarg="--default-key {}".format(keyid)

  homearg = ""
  if homedir:
    homearg = "--homedir {}".format(homedir)

  command = GPG_SIGN_COMMAND.format(keyarg=keyarg, homearg=homearg)
  process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE,
      stdin=subprocess.PIPE, stderr=None)
  signature_data, _ = process.communicate(content)

  signature = parse_signature_packet(signature_data)

  return signature

def gpg_export_pubkey(keyid, homedir = None):

  if keyid is None:
    # FIXME: probably needs smarter parsing of what a valid keyid is so as to
    # not export more than on pubkey packet.
    raise Exception("we need to export an individual keyid. Please provide one")

  homearg = ""
  if homedir:
    homearg = "--homedir {}".format(homedir)

  command = GPG_EXPORT_PUBKEY_COMMAND.format(keyid=keyid, homearg=homearg)
  process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE,
      stdin=subprocess.PIPE, stderr=None)
  key_packet, _ = process.communicate()

  pubkey, keyinfo = parse_pubkey_packet(key_packet)

  return {
    "method": keyinfo['method'],
    "type": keyinfo['type'],
    "hashes": ["pgp+SHA1"],
    "keyid": keyinfo['keyid'],
    "keyval" : {
      "private": "",
      "public": pubkey
      }
    }
