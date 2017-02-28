"""
<Module Name>
  in_toto/artifact_rules.py

<Author>
  Santiago Torres-Arias <santiago@nyu.edu>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Nov 18, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  This module provides functions to ensure the syntax of the matchrules is
  correct.

"""
import six
import securesystemslib.exceptions
import securesystemslib.formats

def unpack_rule(rule):
  """
  Parses the rule and extracts and returns the necessary data to apply the
  rule. Can also be used to verify if a rule complies with any of the formats

  <Arguments>
    rule:
        The rule to be unpacked, one of:
        MATCH <pattern> [IN <source-path-prefix>] WITH (MATERIALS|PRODUCTS)
            [IN <destination-path-prefix>] FROM <step>,
        CREATE <path,
        DELETE <pattern>,
        MODIFY <pattern>,
        ALLOW <pattern>,
        DISALLOW <pattern>

  <Exceptions>
    raises FormatError, if the rule does not comply with any of the formats.

  <Side Effects>
    None.

  <Returns>
    A dictionary of the artifact rule data,
    if it is a generic rule the dictionary is:
    {
      "type": rule[0], i.e.: ("CREATE"|"MODIFY"|"DELETE"|"ALLOW"|"DISALLOW")
      "pattern" : rule[1], i.e. path pattern
    }

    if it is a match rule, the dictionary is:
    {
      "type": rule[0], i.e. "MATCH",
      "pattern": rule[1], i.e. path pattern
      "source_prefix": path or empty string
      "dest_prefix": path or empty string
      "dest_type" : destination artifact type, ("MATERIAL"|"PRODUCT")
      "dest_name": destination step/inspection name
    }

  """

  GENERIC_RULES = {"create", "modify", "delete", "allow", "disallow",}
  COMPLEX_RULES = {"match",}
  ALL_RULES = GENERIC_RULES | COMPLEX_RULES

  if not isinstance(rule, list):
    raise securesystemslib.exceptions.FormatError("Wrong rule format,"
        " rule must be a list.\n"
        "Got: \n\t'{0}'".format(rule))

  rule_len = len(rule)

  if (rule_len < 2 or not isinstance(rule[0], six.string_types) or
      rule[0].lower() not in ALL_RULES):
    raise securesystemslib.exceptions.FormatError("Wrong rule format,"
        " rule must start with one of '{0}' and specify a 'pattern' as"
        " second element.\n"
        "Got: \n\t'{1}'".format(", ".join(ALL_RULES), rule))

  rule_type = rule[0].lower()
  pattern = rule[1]

  if not isinstance(pattern, six.string_types):
    raise securesystemslib.exceptions.FormatError("Wrong rule format,"
        " 'pattern' (second element) must be a string.\n"
        "Got: \n\t'{0}'".format(rule))

  # Type is one of "CREATE", "MODIFY", "DELETE", "ALLOW", "DISALLOW"
  if rule_type in GENERIC_RULES:
    if rule_len != 2:
      raise securesystemslib.exceptions.FormatError("Wrong rule format,"
        " generic rules must have one of the formats:\n\t"
        "CREATE <pattern>\n\t"
        "MODIFY <pattern>\n\t"
        "DELETE <pattern>\n\t"
        "ALLOW <pattern>\n\t"
        "DISALLOW <pattern>\n"
        "Got:\n\t{}".format(rule))
    else:
      return {
        "type": rule_type,
        "pattern": pattern,
      }

  # Type is "MATCH"
  elif rule_type in COMPLEX_RULES:

    # ... IN <source-path-prefix> WITH (MATERIALS|PRODUCTS)
    # IN <destination-path-prefix> FROM <step>
    if (rule_len == 10 and rule[2].lower() == "in" and
        rule[4].lower() == "with" and rule[6].lower() == "in" and
        rule[8].lower() == "from"):
      source_prefix = rule[3]
      dest_type = rule[5]
      dest_prefix = rule[7]
      dest_name = rule[9]

    # ... IN <source-path-prefix> WITH (MATERIALS|PRODUCTS) FROM <step>
    elif (rule_len == 8 and rule[2].lower() == "in" and
        rule[4].lower() == "with" and rule[6].lower() == "from"):
      source_prefix = rule[3]
      dest_type = rule[5]
      dest_prefix = ""
      dest_name = rule[7]

    # ... WITH (MATERIALS|PRODUCTS) IN <destination-path-prefix> FROM <step>
    elif (rule_len == 8 and rule[2].lower() == "with" and
        rule[4].lower() == "in" and rule[6].lower() == "from"):
      source_prefix = ""
      dest_type = rule[3]
      dest_prefix = rule[5]
      dest_name = rule[7]

    # ... WITH (MATERIALS|PRODUCTS) FROM <step>
    elif (rule_len == 6 and rule[2].lower() == "with" and
        rule[4].lower() == "from"):
      source_prefix = ""
      dest_type = rule[3]
      dest_prefix = ""
      dest_name = rule[5]

    else:
      raise securesystemslib.exceptions.FormatError("Wrong rule format,"
          " match rules must have the format:\n\t"
          " MATCH <pattern> [IN <source-path-prefix>] WITH"
          " (MATERIALS|PRODUCTS) [IN <destination-path-prefix>] FROM <step>.\n"
          "Got: \n\t{}".format(rule))

    if not isinstance(dest_type, six.string_types) or (
        dest_type.lower() != "materials" and dest_type.lower() != "products"):
      raise securesystemslib.exceptions.FormatError("Wrong rule format,"
          " match rules must have either MATERIALS or PRODUCTS (case"
          " insensitive) as destination.\n"
          "Got: \n\t{}".format(rule))

    if not isinstance(source_prefix, six.string_types):
      raise securesystemslib.exceptions.FormatError("Wrong rule format,"
          " optional source-path-prefix must be of type String.\n"
          "Got: \n\t{}".format(rule))

    if not isinstance(dest_prefix, six.string_types):
      raise securesystemslib.exceptions.FormatError("Wrong rule format,"
          " optional destination-path-prefix must be of type String.\n"
          "Got: \n\t{}".format(rule))

    if not isinstance(dest_name, six.string_types):
        raise securesystemslib.exceptions.FormatError("Wrong rule format,"
          " step name must be a string.\n"
          "Got: \n\t{}".format(rule))

    return {
      "type": rule_type,
      "pattern": pattern,
      "source_prefix": source_prefix,
      "dest_prefix": dest_prefix,
      "dest_type" : dest_type.lower(),
      "dest_name": dest_name
    }

  #else:
  # can't reach else
  # if it is neither in GENERIC_RULES nor in MATCH_RULES it would
  # have already raised an exception above when checking if it is in ALL_RULES