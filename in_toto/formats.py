# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  formats.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>
  Santiago Torres-Arias <santiago@nyu.edu>

<Started>
  November 28, 2017.

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Helpers to validate API inputs and metadata model objects.

"""
from copy import deepcopy
from re import fullmatch

from securesystemslib.exceptions import FormatError
from securesystemslib.signer import Key, Signature

from in_toto.models._signer import GPGKey, GPGSignature


def _err(arg, expected):
    return FormatError(f"expected {expected}, got '{arg} ({type(arg)})'")


def _check_int(arg):
    if not isinstance(arg, int):
        raise _err(arg, "int")


def _check_str(arg):
    if not isinstance(arg, str):
        raise _err(arg, "str")


def _check_hex(arg):
    _check_str(arg)
    if fullmatch(r"^[0-9a-fA-F]+$", arg) is None:
        raise _err(arg, "hex string")


def _check_list(arg):
    if not isinstance(arg, list):
        raise _err(arg, "list")


def _check_dict(arg):
    if not isinstance(arg, dict):
        raise _err(arg, "dict")


def _check_str_list(arg):
    _check_list(arg)
    for e in arg:
        _check_str(e)


def _check_hex_list(arg):
    _check_list(arg)
    for e in arg:
        _check_hex(e)


def _check_iso8601(arg):
    """Check iso8601 date format."""
    _check_str(arg)
    if fullmatch(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", arg) is None:
        raise _err(arg, "'YYYY-MM-DDTHH:MM:SSZ'")


def _check_hash_dict(arg):
    """Check artifact hash dict."""
    _check_dict(arg)
    for k, v in arg.items():
        _check_str(k)
        _check_hex(v)


def _check_parameter_dict(arg):
    """Check verifylib parameter dict."""
    _check_dict(arg)
    for k, v in arg.items():
        _check_str(k)
        if fullmatch(r"^[a-zA-Z0-9_-]+$", k) is None:
            raise _err(arg, "'a-zA-Z0-9_-'")
        _check_str(v)


def _check_signature(arg):
    """Check signature dict."""
    _check_dict(arg)
    # NOTE: `GPGSignature` and `Signature` serialization formats are incompatible
    try:
        GPGSignature.from_dict(arg)
    except KeyError:
        try:
            Signature.from_dict(deepcopy(arg))
        except KeyError as e:
            raise _err(arg, "signature dict") from e


def _check_public_key(arg):
    """Check public key dict."""
    _check_dict(arg)
    # NOTE: `GPGKey` and `Key` serialization formats are incompatible
    try:
        GPGKey.from_dict(arg["keyid"], arg)
    except (KeyError, TypeError):
        try:
            Key.from_dict(arg["keyid"], deepcopy(arg))
        except KeyError as e:
            raise _err(arg, "public key dict") from e


def _check_public_keys(arg):
    """Check dict of public key dicts."""
    _check_dict(arg)
    for k, v in arg.items():
        _check_hex(k)
        _check_public_key(v)


def _check_signing_key(arg):
    """Check legacy signing key dict format.

    NOTE: signing key dict is deprecated, this check will be removed with it
    """
    _check_public_key(arg)
    if not arg["keyval"].get("private"):
        raise _err(arg, "private key data")
