"""
<Module Name>
  toto/models/validators.py

<Author>
  Santiago Torres-Arias <santiago@nyu.edu>

<Started>
  Nov 18, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  This module provides functions to ensure the syntax of the matchrules is
  correct.

"""
from toto.ssl_commons.exceptions import FormatError
import toto.ssl_crypto.formats

def _validate_match_rule(keywords):
  """ private helper to verify the syntax of the MATCH matchrule """
  MATERIAL_OR_PRODUCT = {'PRODUCT', 'MATERIAL'}

  if not isinstance(keywords, list):
    raise FormatError("this matching rule is not a list")

  if len(keywords) == 5:
    rule, artifact, path_pattern, from_keyword, step = keywords
    as_keyword = "AS"
    target_path_pattern = path_pattern 

  elif len(keywords) == 7:
    (rule, artifact, path_pattern, as_keyword, target_path_pattern, from_keyword,
        step) = keywords
  else:
    raise FormatError("Wrong rule format, should be: MATCH (MATERIAL/PRODUCT)"
      "<path_pattern> [AS <target_path_pattern>] FROM <step>.\n\t"
      "Got: {}".format(" ".join(keywords)))

  if rule != "MATCH" and rule.upper() != "MATCH":
    raise FormatError("Wrong rule to verify! {}".format(rule))

  if from_keyword != "FROM" and from_keyword.upper() != "FROM":
    raise FormatError("FROM should come before step")

  if as_keyword != "AS" and as_keyword.upper() != "AS":
    raise FormatError("AS should come after the step name")

  if artifact not in MATERIAL_OR_PRODUCT and \
      artifact.upper() not in MATERIAL_OR_PRODUCT:
    raise FormatError("Target should be either MATERIAL or PRODUCT!")

def _validate_generic_rule(keywords):
  """ private helper that verifies the syntax of the other rules """

  VALID_OPERATIONS = {'CREATE', 'MODIFY', 'DELETE',}

  if not isinstance(keywords, list):
    raise FormatError("this matching rule is not a list")

  if len(keywords) != 2:
    raise FormatError("Wrong rule format")

  rule, artifact = keywords

  toto.ssl_crypto.formats.PATH_SCHEMA.check_match(artifact)

  if rule not in VALID_OPERATIONS and rule.upper() not in VALID_OPERATIONS:
    raise FormatError("{} is not a valid rule!".format(rule))

def check_matchrule_syntax(keywords):
  """
  <Purpose>
    verify that the syntax of the provided keywords corresponds to the valid
    statements of the matchrules described in the specification

  <Arguments>
    keywords: a list of keywords (e.g., ["CREATE", "foo"]), 

  <Returns>
    None

  <Exceptions>
    FormatError: if the keywords provided do not match the matchrule syntax
  """

  RULE_DISPATCHERS = {'MATCH': _validate_match_rule,
      'CREATE': _validate_generic_rule,
      'MODIFY': _validate_generic_rule,
      'DELETE': _validate_generic_rule
  }

  if not isinstance(keywords, list):
    raise FormatError("Product and Material matchers should be a list!")

  rule = keywords[0].upper()
  if rule not in RULE_DISPATCHERS:
    raise FormatError("error in {}.\n\trule should be one of "
            "{}".format(rule, RULE_DISPATCHERS.keys()))

  return RULE_DISPATCHERS[rule](keywords)
