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
  Format schemas for in-toto metadata, based on securesystemslib.schema.

  The schemas can be verified using the following methods inherited from
  securesystemslib.schema:

  in_toto.gpg.formats.<SCHEMA>.check_match(<object to verify>)
  in_toto.gpg.formats.<SCHEMA>.matches(<object to verify>)

  `check_match` raises a securesystemslib.exceptions.FormatError and `matches`
  returns False if the verified object does not match the schema (True
  otherwise).

"""
import in_toto.gpg.formats as gpg_formats
import securesystemslib.schema as ssl_schema
import securesystemslib.formats as ssl_formats

# Note: Verification keys can have private portions but in case of GPG we
# only have a PUBKEY_SCHEMA (because we never export private gpg keys from
# the gpg keyring)
ANY_VERIFICATION_KEY_SCHEMA = ssl_schema.OneOf([ssl_formats.ANYKEY_SCHEMA,
    gpg_formats.PUBKEY_SCHEMA])

ANY_VERIFICATION_KEY_DICT_SCHEMA = ssl_schema.DictOf(
  key_schema = ssl_formats.KEYID_SCHEMA,
  value_schema = ANY_VERIFICATION_KEY_SCHEMA)

ANY_PUBKEY_SCHEMA = ssl_schema.OneOf([ssl_formats.PUBLIC_KEY_SCHEMA,
    gpg_formats.PUBKEY_SCHEMA])

ANY_PUBKEY_DICT_SCHEMA = ssl_schema.DictOf(
  key_schema = ssl_formats.KEYID_SCHEMA,
  value_schema = ANY_PUBKEY_SCHEMA)

ANY_SIGNATURE_SCHEMA = ssl_schema.OneOf([ssl_formats.SIGNATURE_SCHEMA,
    gpg_formats.SIGNATURE_SCHEMA])

ANY_STRING_SCHEMA = ssl_schema.AnyString()
LIST_OF_ANY_STRING_SCHEMA = ssl_schema.ListOf(ANY_STRING_SCHEMA)

PARAMETER_DICTIONARY_KEY = ssl_schema.RegularExpression(r'[a-zA-Z0-9_-]+')
PARAMETER_DICTIONARY_SCHEMA = ssl_schema.DictOf(
    key_schema = PARAMETER_DICTIONARY_KEY,
    value_schema = ssl_schema.AnyString())
