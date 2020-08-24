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

  in_toto.formats.<SCHEMA>.check_match(<object to verify>)
  in_toto.formats.<SCHEMA>.matches(<object to verify>)

  `check_match` raises a securesystemslib.exceptions.FormatError and `matches`
  returns False if the verified object does not match the schema (True
  otherwise).

"""
import securesystemslib.schema as ssl_schema

PARAMETER_DICTIONARY_KEY = ssl_schema.RegularExpression(r'[a-zA-Z0-9_-]+')
PARAMETER_DICTIONARY_SCHEMA = ssl_schema.DictOf(
    key_schema = PARAMETER_DICTIONARY_KEY,
    value_schema = ssl_schema.AnyString())
