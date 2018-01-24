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
  This module provides functions parse artifact rules and validate their
  syntax.

"""
import in_toto.formats
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
      "rule_type": rule[0] ("CREATE"|"MODIFY"|"DELETE"|"ALLOW"|"DISALLOW")
      "pattern" : rule[1], a path pattern
    }

    if it is a match rule, the dictionary is:
    {
      "rule_type": rule[0],  ("MATCH"),
      "pattern": rule[1], a path pattern
      "source_prefix": path or empty string
      "dest_prefix": path or empty string
      "dest_type" : destination artifact type, ("MATERIAL"|"PRODUCT")
      "dest_name": destination step/inspection name
    }

  """

  GENERIC_RULES = {"create", "modify", "delete", "allow", "disallow",}
  COMPLEX_RULES = {"match",}
  ALL_RULES = GENERIC_RULES | COMPLEX_RULES
  in_toto.formats.LIST_OF_ANY_STRING_SCHEMA.check_match(rule)

  # Create all lower rule copy to case insensitively parse out tokens whose
  # position we don't know yet
  # We keep the original rule to retain the non-token elements' case
  rule_lower = []
  for rule_elem in rule:
    rule_lower.append(rule_elem.lower())

  rule_len = len(rule)

  if rule_len < 2 or rule_lower[0] not in ALL_RULES:
    raise securesystemslib.exceptions.FormatError("Wrong rule format,"
        " rules must start with one of '{0}' and specify a 'pattern' as"
        " second element.\n"
        "Got: \n\t'{1}'".format(", ".join(ALL_RULES), rule))

  rule_type = rule_lower[0]
  pattern = rule[1]

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
        "rule_type": rule_type,
        "pattern": pattern,
      }

  # Type is "MATCH"
  # NOTE: Can't reach `else` branch, if the rule is neither in GENERIC_RULES
  # nor in COMPLEX_RULES an exception is raised earlier.
  elif rule_type in COMPLEX_RULES: # pragma: no branch


    # ... IN <source-path-prefix> WITH (MATERIALS|PRODUCTS)
    # IN <destination-path-prefix> FROM <step>
    if (rule_len == 10 and rule_lower[2] == "in" and
        rule_lower[4] == "with" and rule_lower[6] == "in" and
        rule_lower[8] == "from"):
      source_prefix = rule[3]
      dest_type = rule_lower[5]
      dest_prefix = rule[7]
      dest_name = rule[9]

    # ... IN <source-path-prefix> WITH (MATERIALS|PRODUCTS) FROM <step>
    elif (rule_len == 8 and rule_lower[2] == "in" and
        rule_lower[4] == "with" and rule_lower[6] == "from"):
      source_prefix = rule[3]
      dest_type = rule_lower[5]
      dest_prefix = ""
      dest_name = rule[7]

    # ... WITH (MATERIALS|PRODUCTS) IN <destination-path-prefix> FROM <step>
    elif (rule_len == 8 and rule_lower[2] == "with" and
        rule_lower[4] == "in" and rule_lower[6] == "from"):
      source_prefix = ""
      dest_type = rule_lower[3]
      dest_prefix = rule[5]
      dest_name = rule[7]

    # ... WITH (MATERIALS|PRODUCTS) FROM <step>
    elif (rule_len == 6 and rule_lower[2] == "with" and
        rule_lower[4] == "from"):
      source_prefix = ""
      dest_type = rule_lower[3]
      dest_prefix = ""
      dest_name = rule[5]

    else:
      raise securesystemslib.exceptions.FormatError("Wrong rule format,"
          " match rules must have the format:\n\t"
          " MATCH <pattern> [IN <source-path-prefix>] WITH"
          " (MATERIALS|PRODUCTS) [IN <destination-path-prefix>] FROM <step>.\n"
          "Got: \n\t{}".format(rule))

    if dest_type != "materials" and dest_type != "products":
      raise securesystemslib.exceptions.FormatError("Wrong rule format,"
          " match rules must have either MATERIALS or PRODUCTS (case"
          " insensitive) as destination.\n"
          "Got: \n\t{}".format(rule))

    return {
      "rule_type": rule_type,
      "pattern": pattern,
      "source_prefix": source_prefix,
      "dest_prefix": dest_prefix,
      "dest_type" : dest_type,
      "dest_name": dest_name
    }
