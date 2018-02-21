"""
<Module Name>
  functions.py

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
import logging

import in_toto.gpg.common
from in_toto.gpg.constants import (GPG_EXPORT_PUBKEY_COMMAND, GPG_SIGN_COMMAND,
    SIGNATURE_HANDLERS)

from in_toto.gpg.formats import GPG_HASH_ALGORITHM_STRING

import securesystemslib.formats


# Inherits from in_toto base logger (c.f. in_toto.log)
log = logging.getLogger(__name__)


def gpg_sign_object(content, keyid=None, homedir=None):
  """
  <Purpose>
    Calls the gpg2 command line utility to sign the passed content with the key
    identified by the passed keyid from the gpg keyring at the passed homedir.

    The executed base command is defined in constants.GPG_SIGN_COMMAND.

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
    ValueError: if the gpg command failed to create a valid signature.
    OSError: if the gpg command is not present or non-executable.

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
      stdin=subprocess.PIPE, stderr=subprocess.PIPE)
  signature_data, junk = process.communicate(content)

  signature = in_toto.gpg.common.parse_signature_packet(signature_data)

  # On GPG < 2.1 we cannot derive the keyid from the signature data.
  # Instead we try to compute the keyid from the public part of the signing key
  # Note: This fails if no keyid was passed, e.g. if the default key was used
  # for signing, c.f. `gpg_export_pubkey`.
  # Excluded so that coverage does not vary in different test environments
  if not signature["keyid"]: # pragma: no cover
    log.warning("the created signature has no keyid. We will export the"
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
  in_toto.gpg.formats.PUBKEY_SCHEMA.check_match(pubkey_info)
  in_toto.gpg.formats.SIGNATURE_SCHEMA.check_match(signature_object)

  handler = SIGNATURE_HANDLERS[pubkey_info['type']]
  return handler.gpg_verify_signature(signature_object, pubkey_info, content)


def gpg_export_pubkey(keyid, homedir=None):
  """
  <Purpose>
    Calls gpg2 command line utility to export the gpg public key identified by
    the passed keyid from the gpg keyring at the passed homedir in a format
    suitable for in-toto.

    The executed base command is defined in
    constants.GPG_EXPORT_PUBKEY_COMMAND.

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
            " Please provide a valid keyid! Keyid was '{}'.".format(keyid))

  homearg = ""
  if homedir:
    homearg = "--homedir {}".format(homedir)

  command = GPG_EXPORT_PUBKEY_COMMAND.format(keyid=keyid, homearg=homearg)
  process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE,
      stdin=subprocess.PIPE, stderr=subprocess.PIPE)
  key_packet, junk = process.communicate()

  pubkey, keyinfo = in_toto.gpg.common.parse_pubkey_packet(key_packet)

  return {
    "method": keyinfo['method'],
    "type": keyinfo['type'],
    "hashes": [GPG_HASH_ALGORITHM_STRING],
    "keyid": keyinfo['keyid'],
    "keyval" : {
      "private": "",
      "public": pubkey
      }
    }
