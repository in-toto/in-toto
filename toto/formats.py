"""
<Program Name>
  formats.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Jul 15, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Currently unused!!
  Used to define schemas for toto metadata files using ssl_commons.schema
  before we moved to OO
"""

# LAYOUT_SCHEMA
import ssl_commons.schema
import ssl_crypto.formats

# Schema for link-[hash].json
LINK_METADATA_FILENAME_SCHEMA = ssl_commons.schema.RegularExpression(r'link-[a-fA-F0-9]+\.json')

# Link command is either a list, containing a command and options or
# a keyword (e.g. "edit") for a command-less toto-run that uses a pre-recorded
# repository state to hash materials and the current state to hash products

LINK_COMMAND_SCHEMA = ssl_commons.schema.OneOf(
  "edit",
  ssl_commons.schema.ListOf(
    min_count = 1,
    schema = ssl_commons.schema.Any()
  )
)

LINK_STATE_SCHEMA = ssl_commons.schema.ListOf(
  ssl_commons.schema.DictOf(
      key_schema = ssl_crypto.formats.PATH_SCHEMA,
      value_schema = ssl_crypto.formats.HASH_SCHEMA
  )
)

LINK_TRANSFORMATIONS_SCHEMA = ssl_commons.schema.ListOf(
  ssl_commons.schema.DictOf(
    key_schema = ssl_crypto.formats.PATH_SCHEMA,
    value_schema = ssl_commons.schema.Struct(
      ssl_commons.schema.OneOf(
        "add",
        "transform",
        "remove"
      ),
      ssl_crypto.formats.HASH_SCHEMA
    )
  )
)

LINK_METADATA_SCHEMA = ssl_commons.schema.Object(
  object_name = 'LINK_METADATA_SCHEMA',
  _type = SCHEMA.String('link'),
  # version = ssl_crypto.formats.METADATAVERSION_SCHEMA, # XXX: Are we sure we want a version here?
  command = LINK_COMMAND_SCHEMA,
  branch = ssl_crypto.formats.HASH_SCHEMA,
  ssl_commons.schema.DictOf(
    key_schema = ssl_commons.schema.String("materials-hash"),
    value_schema = ssl_crypto.formats.HASH_SCHEMA
  ),
  transformations = TRANSFORMATIONS_SCHEMA,
  ssl_commons.schema.DictOf(
    key_schema = ssl_commons.schema.String("transformation-hash"),
    value_schema = ssl_crypto.formats.HASH_SCHEMA,
  ),
  report = ssl_commons.schema.Any() # XXX: Need to decide on format
)