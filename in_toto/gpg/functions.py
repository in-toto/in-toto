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

import in_toto.log
from in_toto.gpg.constants import (GPG_EXPORT_PUBKEY_COMMAND, GPG_SIGN_COMMAND,
    SIGNATURE_HANDLERS)
from in_toto.gpg.common import parse_signature_packet, parse_pubkey_packet

import securesystemslib.formats


def gpg_sign_object(content, keyid=None, homedir=None):
  """
  <Purpose>
    Calls gpg command line utility to sign the passed content with the key
    identified by the passed keyid from the gpg keyring at the passed homedir.

  <Arguments>
    content:
            The content to be signed. (bytes)

    keyid: (optional)
            The keyid of the gpg signing keyid. If not passed the default
            key in the keyring is used.
            Note: On not fully supported gpg versions the keyid must be passed.

    homedir: (optional)
            Path to the gpg keyring. If not passed the default keyring is used.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    The created signature in the format: gpg.formats.SIGNATURE_SCHEMA.
  """

  keyarg = ""
  if keyid:
    keyarg = "--default-key {}".format(keyid)

  homearg = ""
  if homedir:
    homearg = "--homedir {}".format(homedir)

  command = GPG_SIGN_COMMAND.format(keyarg=keyarg, homearg=homearg)
  process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE,
      stdin=subprocess.PIPE, stderr=None)
  signature_data, _ = process.communicate(content)

  signature = parse_signature_packet(signature_data)

  # On GPG < 2.1 we cannot derive the keyid from the signature data.
  # Instead we try to compute the keyid from the public part of the signing key
  # Note: This fails if no keyid was passed, e.g. if the default key was used
  # for signing, c.f. `gpg_export_pubkey`.
  # Excluded so that coverage does not vary in different test environments
  if not signature["keyid"]: # pragma: no cover
    in_toto.log.warn("the created signature has no keyid. We will export the"
        " public portion of the signing key to compute the keyid.")
    signature["keyid"] = gpg_export_pubkey(keyid, homedir)["keyid"]

  return signature


def gpg_verify_signature(signature_object, pubkey_info, content):
  """
  <Purpose>
    Verifies the passed signature against the passed content using the
    passed public key.

    The function selects the appropriate verification algorithm (rsa or dsa)
    based on the "type" field in the passed public key object.

  <Arguments>
    signature_object:
            A signature object in the format: gpg.formats.SIGNATURE_SCHEMA

    pubkey_info:
            A public key object in the format: gpg.formats.PUBKEY_SCHEMA

    content:
            The content to be verified. (bytes)

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    True if signature verification passes, False otherwise.

  """
  handler = SIGNATURE_HANDLERS[pubkey_info['type']]
  return handler.gpg_verify_signature(signature_object, pubkey_info, content)


def gpg_export_pubkey(keyid, homedir=None):
  """
  <Purpose>
    Calls gpg command line utility to export the gpg public key identified by
    the passed keyid from the gpg keyring at the passed homedir in a format
    suitable for in-toto.

  <Arguments>
    keyid:
            The GPG keyid in format: securesystemslib.formats.KEYID_SCHEMA

    homedir: (optional)
            Path to the gpg keyring. If not passed the default keyring is used.

  <Exceptions>
    Value Error if the keyid does not match the required format

  <Side Effects>
    None.

  <Returns>
    The exported public key object in the format: gpg.formats.PUBKEY_SCHEMA

  """
  if not securesystemslib.formats.KEYID_SCHEMA.matches(keyid):
    # FIXME: probably needs smarter parsing of what a valid keyid is so as to
    # not export more than one pubkey packet.
    raise ValueError("we need to export an individual key."
            " Please provide a valid keyid! Keyid was '{}'".format(keyid))

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
