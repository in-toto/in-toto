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
import toto.models.matchrule
import toto.ssl_crypto.keys
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


def _verify_rules(rules, source_type, item_name, item_link, step_links):
  """Internal helper function to iterate over a list of Matchrules and
  verify them."""

  for rule_data in rules:
    rule = toto.models.matchrule.Matchrule.read(rule_data)
    rule.source_type = source_type
    rule.verify_rule(item_link, step_links)


def verify_all_item_rules(items, source_links, target_links):
  """
  <Purpose>
    Iteratively verifies material matchrules and product matchrules of
    passed items (Steps or Inspections).
    Artificats in source links are usually matched with artifacts in
    target links according to the rules defined in the item.

  <Arguments>
    items:
            A list of either Step or Inspection objects
    source_links:
            A dictionary of Link metadata objects with Link names as keys.
    target_links:
            A dictionary of Link metadata objects with Link names as keys.

  <Exceptions>
    raises an Exception if a matchrule does not verify.
    TBA (see https://github.com/in-toto/in-toto/issues/6)

  <Side Effects>
    Calls matchrule verification methods.

  """
  for item in items:
    source_link = source_links[item.name]
    _verify_rules(item.material_matchrules, "material",
        item.name, source_link, target_links)

    _verify_rules(item.product_matchrules, "product",
        item.name, source_link, target_links)



