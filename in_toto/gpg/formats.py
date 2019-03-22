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
  Format schemas for gpg data structures (keys, signatures)
  based on securesystemslib.schema.

  The schemas can be verified using the following methods inherited from
  securesystemslib.schema:

  in_toto.gpg.formats.<SCHEMA>.check_match(<object to verify>)
  in_toto.gpg.formats.<SCHEMA>.matches(<object to verify>)

  `check_match` raises a securesystemslib.exceptions.FormatError and `matches`
  returns False if the verified object does not match the schema (True
  otherwise).


  Example Usage:

  >>> rsa_pubkey = {
      'type': 'rsa',
      'hashes': ['pgp+SHA2'],
      'keyid': '8465a1e2e0fb2b40adb2478e18fb3f537e0c8a17',
      'keyval': {
        'public': {
          'e': u'010001',
          'n': (u'da59409e6ede307a52f6851954a7bd4b9e309bd40a390f8c0de9722b63101
                  10ef0b095bf1c473e33db97150edae05c63dda70c03902701b15f3c5c3089
                  47e1b06675b4f1112030f1145be84ae1562e9120c2d429b20d5056337cbc9
                  7fc8b5db5704a21db635d00b2157ed68a403c793e9958b77e00163f99b018
                  09e08ee9099b99b117c086501e79eb947f760a0715bead0024c48d81f9000
                  671c4306a93725965f3ff2dc9806eaf081357f0268cab8ba7582d2e95e512
                  25a9dc7ed31a9568c45568d7917b05e7c954d561cd084291e77a7bdd69e3a
                  c2f9091de55fe3f4e730147e880e2fc044c5f7c04c75ce33a3c0b52380f4d
                  60309708c56185f3bce6703b')
          },
        'private': ''
      },
      'method': 'pgp+rsa-pkcsv1.5'
    }
  >>> RSA_PUBKEY_SCHEMA.matches(rsa)
  True

"""
import securesystemslib.schema as ssl_schema
import securesystemslib.formats as ssl_formats


def _create_pubkey_with_subkey_schema(pubkey_schema):
  """Helper method to extend the passed public key schema with an optional
  dictionary of sub public keys "subkeys" with the same schema."""
  schema = pubkey_schema
  subkey_schema_tuple =  ("subkeys", ssl_schema.Optional(
        ssl_schema.DictOf(
          key_schema=ssl_formats.KEYID_SCHEMA,
          value_schema=pubkey_schema
          )
        )
      )
  # Any subclass of `securesystemslib.schema.Object` stores the schemas that
  # define the attributes of the object in its `_required` property, even if
  # such a schema is of type `Optional`.
  # TODO: Find a way that does not require to access a protected member
  schema._required.append(subkey_schema_tuple) # pylint: disable=protected-access
  return schema


GPG_HASH_ALGORITHM_STRING = "pgp+SHA2"
PGP_RSA_PUBKEY_METHOD_STRING = "pgp+rsa-pkcsv1.5"
PGP_DSA_PUBKEY_METHOD_STRING = "pgp+dsa-fips-180-2"

RSA_PUBKEYVAL_SCHEMA = ssl_schema.Object(
  object_name = "RSA_PUBKEYVAL_SCHEMA",
  e = ssl_schema.AnyString(),
  n = ssl_formats.HEX_SCHEMA
)


# We have to define RSA_PUBKEY_SCHEMA in two steps, because it is
# self-referential. Here we define a shallow _RSA_PUBKEY_SCHEMA, which we use
# below to create the self-referential RSA_PUBKEY_SCHEMA.
_RSA_PUBKEY_SCHEMA = ssl_schema.Object(
  object_name = "RSA_PUBKEY_SCHEMA",
  type = ssl_schema.String("rsa"),
  method = ssl_schema.String(PGP_RSA_PUBKEY_METHOD_STRING),
  hashes = ssl_schema.ListOf(ssl_schema.String(GPG_HASH_ALGORITHM_STRING)),
  keyid = ssl_formats.KEYID_SCHEMA,
  keyval = ssl_schema.Object(
      public = RSA_PUBKEYVAL_SCHEMA,
      private = ssl_schema.String("")
    )
)
RSA_PUBKEY_SCHEMA = _create_pubkey_with_subkey_schema(
    _RSA_PUBKEY_SCHEMA)


DSA_PUBKEYVAL_SCHEMA = ssl_schema.Object(
  object_name = "DSA_PUBKEYVAL_SCHEMA",
  y = ssl_formats.HEX_SCHEMA,
  p = ssl_formats.HEX_SCHEMA,
  q = ssl_formats.HEX_SCHEMA,
  g = ssl_formats.HEX_SCHEMA
)


# We have to define DSA_PUBKEY_SCHEMA in two steps, because it is
# self-referential. Here we define a shallow _DSA_PUBKEY_SCHEMA, which we use
# below to create the self-referential DSA_PUBKEY_SCHEMA.
_DSA_PUBKEY_SCHEMA = ssl_schema.Object(
  object_name = "DSA_PUBKEY_SCHEMA",
  type = ssl_schema.String("dsa"),
  method = ssl_schema.String(PGP_DSA_PUBKEY_METHOD_STRING),
  hashes = ssl_schema.ListOf(ssl_schema.String(GPG_HASH_ALGORITHM_STRING)),
  keyid = ssl_formats.KEYID_SCHEMA,
  keyval = ssl_schema.Object(
      public = DSA_PUBKEYVAL_SCHEMA,
      private = ssl_schema.String("")
    )
)
DSA_PUBKEY_SCHEMA = _create_pubkey_with_subkey_schema(
    _DSA_PUBKEY_SCHEMA)


PUBKEY_SCHEMA = ssl_schema.OneOf([RSA_PUBKEY_SCHEMA,
    DSA_PUBKEY_SCHEMA])


SIGNATURE_SCHEMA = ssl_schema.Object(
    object_name = "SIGNATURE_SCHEMA",
    keyid = ssl_formats.KEYID_SCHEMA,
    short_keyid = ssl_schema.Optional(ssl_formats.KEYID_SCHEMA),
    other_headers = ssl_formats.HEX_SCHEMA,
    signature = ssl_formats.HEX_SCHEMA,
    info = ssl_schema.Optional(ssl_schema.Any()),
  )
