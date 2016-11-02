"""
<Program Name>
  verifylib.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  June 28, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>

  Provides a library to verify a Toto final product containing
  a software supply chain layout.

  The library provides functions to:
    - verify signatures of a layout
    - verify signatures of a link
    - verify if the expected command of a step aligns with the actual command
      as recorded in the link metadata file.
    - run inspections (records link metadata)
    - verify product or material matchrules for steps or inspections

"""

import sys
import datetime
import iso8601
from dateutil import tz

import toto.util
import toto.runlib
import toto.models.layout
import toto.models.link
import toto.ssl_crypto.keys
from toto.exceptions import RuleVerficationFailed
from toto.models.common import ComparableHashDict
import toto.log as log


def run_all_inspections(layout):
  """
  <Purpose>
    Extracts all inspections from a passed Layout's inspect field and
    iteratively runs each inspections command as defined in the in Inspection's
    run field using in-toto runlib.  This producces link metadata which is
    returned as a dictionary with the according inspection names as keys and
    the Link metadata objects as values.

  <Arguments>
    layout:
            A Layout object which is used to extract the Inpsections.

  <Exceptions>
    TBA (see https://github.com/in-toto/in-toto/issues/6)

  <Side Effects>
    Executes the Inspection command and produces Link metadata.

  <Returns>
    A dictionary containing one Link metadata object per Inspection where
    the key is the Inspection name.
  """
  inspection_links_dict = {}
  for inspection in layout.inspect:
    # XXX LP: What should we record as material/product?
    # Is the current directory a sensible default? In general?
    # If so, we should propably make it a default in run_link
    # We could use matchrule paths
    link = toto.runlib.run_link(inspection.name, '.', '.',
        inspection.run.split())
    inspection_links_dict[inspection.name] = link
  return inspection_links_dict

def verify_layout_expiration(layout):
  """
  <Purpose>
    Raises an exception if the passed layout has expired, i.e. if its
    "expire" property is lesser "now".
    Time zone aware datetime objects in UTC+00:00 (Zulu Time) are used.

  <Arguments>
    layout:
            The Layout object to be verified.

  <Exceptions>
    TBA (see https://github.com/in-toto/in-toto/issues/6)

  <Side Effects>
    None

  """
  expire_datetime = iso8601.parse_date(layout.expires)
  if expire_datetime < datetime.datetime.now(tz.tzutc()):
    # raise LayoutExpiredError
    raise Exception("Layout expired")


def verify_layout_signatures(layout, keys_dict):
  """
  <Purpose>
    Iteratively verifies all signatures of a Layout object using the passed
    keys.

  <Arguments>
    layout:
            A Layout object whose signatures are verified.
    keys_dict:
            A dictionary of keys to verify the signatures conformant with
            ssl_crypto.formats.KEYDICT_SCHEMA.

  <Exceptions>
    Raises an exception if a needed key can not be found in the passed
    keys_dict or if a verification fails.
    TBA (see https://github.com/in-toto/in-toto/issues/6)

  <Side Effects>
    Verifies cryptographic Layout signatures.

  """
  layout.verify_signatures(keys_dict)


def verify_link_signatures(link, keys_dict):
  """
  <Purpose>
    Iteratively verifies all signatures of a Link object using the passed
    keys.

  <Arguments>
    link:
            A Link object whose signatures are verified.
    keys_dict:
            A dictionary of keys to verify the signatures conformant with
            ssl_crypto.formats.KEYDICT_SCHEMA.

  <Exceptions>
    Raises an exception if a needed key can not be found in the passed
    keys_dict or if a verification fails.
    TBA (see https://github.com/in-toto/in-toto/issues/6)

  <Side Effects>
    Verifies cryptographic Link signatures.

  """
  link.verify_signatures(keys_dict)


def verify_all_steps_signatures(layout, links_dict):
  """
  <Purpose>
    Extracts the Steps of a passed Layout and iteratively verifies the
    the signatures of the Link object related to each Step by the name field.
    The public keys used for verification are also extracted from the Layout.

  <Arguments>
    layout:
            A Layout object whose Steps are extracted and verified.
    links_dict:
            A dictionary of Link metadata objects with Link names as keys.

  <Exceptions>
    Raises an exception if a needed key can not be found in the passed
    keys_dict or if a verification fails.
    TBA (see https://github.com/in-toto/in-toto/issues/6)

  <Side Effects>
    Verifies cryptographic Link signatures related to Steps of a Layout.

  """
  for step in layout.steps:
    # Find the according link for this step
    link = links_dict[step.name]

    # Create the dictionary of keys for this step
    keys_dict = {}
    for keyid in step.pubkeys:
      keys_dict[keyid] = layout.keys[keyid]

    # Verify link metadata file's signatures
    verify_link_signatures(link, keys_dict)


def verify_command_alignment(command, expected_command):
  """
  <Purpose>
    Checks if two commands align.  The commands align if all of their elements
    are equal.  The commands align in a relaxed fashion if they have different
    lengths and the first x elements of both commands are equal. X being
    min(len(command), len(expected_command)).

  <Arguments>
    command:
            A command list, e.g. ["vi", "foo.py"]
    expected_command:
            A command list, e.g. ["vi"]

  <Exceptions>
    raises an Exception if the commands don't align
    prints a warning if the commands align in a relaxed fashioin
    TBA (see https://github.com/in-toto/in-toto/issues/6)

  <Side Effects>
    Performs string comparison of two lists.

  """
  command_len = len(command)
  expected_command_len = len(expected_command)

  for i in range(min(command_len, expected_command_len)):
    if command[i] != expected_command[i]:
      raise Exception("Command '%s' and expected command '%s' do not align" \
          % (command, expected_command))
  if command_len != expected_command_len:
    log.warning("Command '%s' and expected command '%s' do not fully align" \
        % (command, expected_command))


def verify_all_steps_command_alignment(layout, links_dict):
  """
  <Purpose>
    Iteratively checks if all expected commands as defined in the
    Steps of a Layout align with the actual commands as recorded in the Link
    metadata.

    Note:
      Command alignment is a weak guarantee. Because a functionary can easily
      alias commands.

  <Arguments>
    layout:
            A Layout object to extract the expected commands from.
    links_dict:
            A dictionary of Link metadata objects with Link names as keys.

  <Exceptions>
    raises an Exception if the commands don't align
    prints a warning if the commands align in a relaxed fashioin
    TBA (see https://github.com/in-toto/in-toto/issues/6)

  <Side Effects>
    Performs string comparison of two lists.

  """
  for step in layout.steps:
    # Find the according link for this step
    link = links_dict[step.name]
    command = link.command
    expected_command = step.expected_command.split()
    verify_command_alignment(command, expected_command)


def verify_match_rule(rule, source_type, source_link, target_links):
  """
  <Purpose>
    Verifies that the source artifact (depending on the list the rule was
    extracted from a material or product) hash matches the target artifact
    (depending on the 2nd element of the rule a material or product).

    Also verifies:
    That the target_link as idetfied by ("FROM" <step>) exists in
    the passed target_links dictionary.
    That the source artifact was recorded in the source and target link.

    In case the ("AS", "<target_path>") part of the rule is omitted the
    specified path (3rd element of the rule) is used for target and source.

  <Arguments>
    rule:
          The rule to be verified. Format is one of:
            ["MATCH", "MATERIAL", "<path>", "FROM", "<step>"]
            ["MATCH", "PRODUCT", "<path>", "FROM", "<step>"]
            ["MATCH", "MATERIAL", "<source_path>", "AS",
                "<target_path>", "FROM", "<step>"]
            ["MATCH", "PRODUCT", "<source_path>", "AS",
                "<target_path>", "FROM", "<step>"]

    source_type:
            A string to identify if the rule is a material matchrule or
            product matchrule. One of "material" or "product".

    source_link:
            The Link object for an Item (Step or Inspection) that contains the
            rules to be verified.
            The contained materials and products are used as verification source.

    target_links:
            A dictionary of Link objects with Link names as keys.
            The Link objects relate to Steps.
            The contained materials and products are used as verification target.

  <Exceptions>
    raises an Exception if the rule is not conformant with the rule format.
    raises an if a matchrule does not verify.
    TBA (see https://github.com/in-toto/in-toto/issues/6)

    RuleVerficationFailed

  <Side Effects>
    None.

  """
  # FIXME: Validate rule format

  source_type = source_type.lower()
  source_path = rule[2]
  target_path = rule[4] if len(rule) == 7 else source_path
  target_type = rule[1].lower()
  target_name = rule[-1]

  # Extract source artifacts from source link
  if source_type == "material":
    source_artifacts = source_link.materials
  elif source_type == "product":
    source_artifacts = source_link.products
  else:
    raise Exception("Wrong source type '%s'. Has to be 'material' or 'product'"
        % source_type)

  # Extract target artifacts from target links
  if target_type == "material":
    target_artifacts = target_links[target_name].materials
  elif target_type == "product":
    target_artifacts = target_links[target_name].products
  else:
    # Note: We should never reach this because rule format was validate before
    raise Exception("Wrong target type '%s'. Has to be 'material' or 'product'"
        % source_type)

  # Verify that the source artifact was recorded as material or product
  # in the step this rule was defined for.
  if (source_path not in source_artifacts.keys()):
    raise RuleVerficationFailed("'%s' of link '%s' not in source %ss" \
        % (source_path, source_link.name, source_type))

  # Verify that the Link metadata object which contains the material or product
  # to match with exists.
  if (target_name not in target_links.keys()):
    raise RuleVerficationFailed("'%s' not in target links" \
        % target_name)

  # Verify that the target Link metadata object contains the material or product
  # to match with.
  if (target_path not in target_artifacts.keys()):
    raise RuleVerficationFailed("'%s' not in target %ss" \
        % (target_path, target_type))

  # Verify that the recorded source artifact hash and the recorded target
  # artifact hash are equal.
  if (ComparableHashDict(source_artifacts[source_path]) != \
      ComparableHashDict(target_artifacts[target_path])):
    raise RuleVerficationFailed("hash of source '%s' does not match hash"
        " of target '%s'" % (source_path, target_path))


def verify_create_rule(rule, link):
  """
  <Purpose>
    Verifies that the path (2nd element in rule list) is not found in the
    material list but is found in the product list of the passed Link object,
    i.e. the file was created in the step the rule was defined for.

  <Arguments>
    rule:
            The rule to be verified. Format is: ["CREATE", "<path>"]

    link:
            The Link object for the Item (Step or Inspection) that contains
            the rule.

  <Exceptions>
    raises an Exception if the rule is not conformant with the rule format.
    raises an if a matchrule does not verify.
    TBA (see https://github.com/in-toto/in-toto/issues/6)

    RuleVerficationFailed

  <Side Effects>
    None.

  """
  # FIXME: Validate rule format
  path = rule[1]
  if (path in link.materials.keys()):
    raise RuleVerficationFailed("'%s' " \
        "found in materials of link '%s'" % (path, link.name))

  if (path not in link.products.keys()):
    raise RuleVerficationFailed("'%s' not found in products of link '%s' "
        "- should have been created" % (path, link.name))


def verify_delete_rule(rule, link):
  """
  <Purpose>
    Verifies that the path (2nd element in rule list) is found in the material
    and not in the product list of the passed Link object, i.e. the file was
    deleted in the step the rule was defined for.

  <Arguments>
    rule:
            The rule to be verified. Format is: ["DELETE", "<path>"]

    link:
            The Link object for the Item (Step or Inspection) that contains
            the rule.

  <Exceptions>
    raises an Exception if the rule is not conformant with the rule format.
    raises an if a matchrule does not verify.
    TBA (see https://github.com/in-toto/in-toto/issues/6)

    RuleVerficationFailed

  <Side Effects>
    None.

  """
  # FIXME: Validate rule format

  path = rule[1]
  if (path not in link.materials.keys()):
    raise RuleVerficationFailed("'%s' " \
        "not found in materials of link '%s'" % (path, link.name))

  if (path in link.products.keys()):
    raise RuleVerficationFailed("'%s' found in products of link '%s' "
        "- should have been deleted" % (path, link.name))


def verify_modify_rule(rule, link):
  """
  <Purpose>
    Verifies that the path (2nd element in rule list) is found in the materials
    and products list of the passed Link object and that the hashes of the
    according material and product are not equal, i.e. the file was modified in
    the step the rule was defined for.

  <Arguments>
    rule:
            The rule to be verified. Format is: ["MODIFY", "<path>"]

    link:
            The Link object for the Item (Step or Inspection) that contains
            the rule.

  <Exceptions>
    raises an Exception if the rule is not conformant with the rule format.
    raises an if a matchrule does not verify.
    TBA (see https://github.com/in-toto/in-toto/issues/6)

    RuleVerficationFailed

  <Side Effects>
    None.

  """
  # FIXME: Validate rule format

  path = rule[1]

  if (path not in link.materials.keys()):
    raise RuleVerficationFailed("'%s' " \
        "not found in materials of link '%s'" % (path, link.name))

  if (path not in item_link.products.keys()):
    raise RuleVerficationFailed("'%s' "
        "not found in products of link '%s'" % (path, link.name))

  if (ComparableHashDict(link.materials[path]) == \
      ComparableHashDict(link.products[path])):
    raise RuleVerficationFailed("hashes of product and material '%s' of link "
        "'%s' match - should have been modified" % (path, link.name))


def _verify_rules(rules, source_type, source_link, target_links):
  """
  <Purpose>
    Helper method to iteratively verify all rules of a type.

  <Arguments>
    rules:
            A list containing rules defined in the material_matchrules or
            product_matchrules field of a Step or Inspection object.

    source_type:
            A string to identify if the rule is a material matchrule or
            product matchrule. One of "material" or "product".

    source_link:
            The Link object for an Item (Step or Inspection) that contains the
            rules to be verified.
            The contained materials and products are used as verification source.

    target_links:
            A dictionary of Link objects with Link names as keys.
            The Link objects relate to Steps.
            The contained materials and products are used as verification target.

  <Exceptions>
    raises an Exception if a rule is not conformant with the rule format.
    raises an Exception if a matchrule does not verify.
    TBA (see https://github.com/in-toto/in-toto/issues/6)

  <Side Effects>
    Calls the respective verify_<rule-type>_rule function.

  """
  for rule in rules:
    #FIXME: Validate rule format
    if rule[0].lower() == "match":
      verify_match_rule(rule, source_type, source_link, target_links)

    elif rule[0].lower() == "create":
      verify_create_rule(rule, source_link)

    elif rule[0].lower() == "delete":
      verify_delete_rule(rule, source_link)

    elif rule[0].lower() == "modify":
      verify_modify_rule(rule, source_link)

    else:
      # Note: We should never get here since the rule format was verified before
      raise Exception("Invalid Matchrule", rule)



def verify_all_item_rules(items, source_links, target_links):
  """
  <Purpose>
    Iteratively verifies material matchrules and product matchrules of
    passed items (Steps or Inspections).
    In case of MATCH matchrules an artifact from a source link is matched
    against an artifact from a target link.
    In case of CREATE, DELETE and MODIFY matchrules a source link material
    is matched with a target material.

  <Arguments>
    items:
            A list containing Step and/or Inspection objects

    source_links:
            A dictionary of Link objects with Link names as keys.
            The Link objects can relate to Steps or Inspections.
            The contained materials and products are used as verification source.

    target_links:
            A dictionary of Link objects with Link names as keys.
            The Link objects relate to Steps.
            The contained materials and products are used as verification target.

  <Exceptions>
    raises an Exception if a matchrule does not verify.
    TBA (see https://github.com/in-toto/in-toto/issues/6)

  <Side Effects>
    Calls helper functions to verify all matchrules of an item.

  """
  for item in items:
    source_link = source_links[item.name]
    _verify_rules(item.material_matchrules, "material",
        source_link, target_links)

    _verify_rules(item.product_matchrules, "product",
        source_link, target_links)



