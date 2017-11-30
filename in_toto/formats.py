"""
<Program Name>
  formats.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  November 28, 2017.

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Format schemas for in-toto metadata, based on securesystemslib.schema.

"""
import in_toto.gpg.formats as gpg_formats
import securesystemslib.schema as ssl_schema
import securesystemslib.formats as ssl_formats

# Note: Verification keys can have private portions but in case of GPG we
# only have a PUBKEY_SCHEMA (because we never export private gpg keys from
# the gpg keyring)
ANY_VERIFY_KEY_SCHEMA = ssl_schema.OneOf([ssl_formats.ANYKEY_SCHEMA,
    gpg_formats.PUBKEY_SCHEMA])

ANY_VERIFY_KEY_DICT_SCHEMA = ssl_schema.DictOf(
  key_schema = ssl_formats.KEYID_SCHEMA,
  value_schema = ANY_VERIFY_KEY_SCHEMA)

ANY_PUBKEY_SCHEMA = ssl_schema.OneOf([ssl_formats.PUBLIC_KEY_SCHEMA,
    gpg_formats.PUBKEY_SCHEMA])

ANY_PUBKEY_DICT_SCHEMA = ssl_schema.DictOf(
  key_schema = ssl_formats.KEYID_SCHEMA,
  value_schema = ANY_PUBKEY_SCHEMA)
