"""
<Program Name>
  verifylib.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>
  Santiago Torres-Arias <santiago@nyu.edu>

<Started>
  June 28, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>

  Provides a library to verify an in-toto final product containing
  a software supply chain layout.

  Take a look at `in_toto_verify`'s docstring for more details about the
  entire verification workflow.

"""

import os
import datetime
import iso8601
import fnmatch
import six
import logging
from dateutil import tz

import securesystemslib.exceptions

import in_toto.settings
import in_toto.util
import in_toto.runlib
import in_toto.models.layout
import in_toto.models.link
import in_toto.formats
from in_toto.models.metadata import Metablock
from in_toto.models.link import (FILENAME_FORMAT, FILENAME_FORMAT_SHORT)
from in_toto.models.layout import SUBLAYOUT_LINK_DIR_FORMAT
from in_toto.exceptions import (RuleVerificationError, LayoutExpiredError,
    ThresholdVerificationError, BadReturnValueError,
    SignatureVerificationError)
import in_toto.rulelib

# Inherits from in_toto base logger (c.f. in_toto.log)
log = logging.getLogger(__name__)

RULE_TRACE = {}


def _raise_on_bad_retval(return_value, command=None):
  """
  <Purpose>
    Internal function that checks return values of shell commands, e.g. from
    inspections. Raises exception if the passed value is non-int and non-zero.

  <Arguments>
    return_value:
            The return value to be verified
    command: (optional)
            The command whose execution returned the value, used for exception
            message.

  <Exceptions>
    BadReturnValueError if the return_value is non-int and non-zero

  <Side Effects>
    None.

  <Returns>
    None.
  """

  msg = "Got non-{what} " + "return value '{}'".format(return_value)
  if command:
    msg = "{0} from command '{1}'.".format(msg, command)
  else:
    msg = "{0}.".format(msg)

  if not isinstance(return_value, int):
    raise BadReturnValueError(msg.format(what="int"))

  # TODO: in-toto specification suggests special behavior on
  # return_value == 127, but does not fully define that behavior yet

  if return_value != 0:
    raise BadReturnValueError(msg.format(what="zero"))


def load_links_for_layout(layout, link_dir_path):
  """
  <Purpose>
    Try to load all existing metadata files for each Step of the Layout
    from the current directory.

    For each step the metadata might consist of multiple (thresholds) Link
    or Layout (sub-layouts) files.

  <Arguments>
    layout:
          Layout object

    link_dir_path:
          A path to directory where links are loaded from


  <Side Effects>
    Calls function to read files from disk

  <Exceptions>
    in_toto.exceptions.LinkNotFoundError,
            if fewer than `threshold` link files can be found for any given
            step of the supply chain (preliminary threshold check)

  <Returns>
    A dictionary carrying all the found metadata corresponding to the
    passed layout, e.g.:

    {
      <step name> : {
        <functionary key id> : <Metablock containing a Link or Layout object>,
        ...
      }, ...
    }


  """
  steps_metadata = {}

  # Iterate over all the steps in the layout
  for step in layout.steps:
    links_per_step = {}

    # We try to load a link for every authorized functionary, but don't fail
    # if the file does not exist (authorized != required)
    # FIXME: Should we really pass on IOError, or just skip inexistent links?
    for authorized_keyid in step.pubkeys:
      # Iterate over the authorized key and if present over subkeys
      for keyid in [authorized_keyid] + list(layout.keys.get(authorized_keyid,
          {}).get("subkeys", {}).keys()):

        filename = FILENAME_FORMAT.format(step_name=step.name, keyid=keyid)
        filepath = os.path.join(link_dir_path, filename)

        try:
          metadata = Metablock.load(filepath)
          links_per_step[keyid] = metadata

        except IOError:
          pass

    # This is only a preliminary threshold check, based on (authorized)
    # filenames, to fail early. A more thorough signature-based threshold
    # check is indispensable.
    if len(links_per_step) < step.threshold:
      raise in_toto.exceptions.LinkNotFoundError("Step '{0}' requires '{1}'"
          " link metadata file(s), found '{2}'."
          .format(step.name, step.threshold, len(links_per_step)))

    steps_metadata[step.name] = links_per_step

  return steps_metadata


def run_all_inspections(layout):
  """
  <Purpose>
    Extracts all inspections from a passed Layout's inspect field and
    iteratively runs each command defined in the Inspection's `run` field using
    `runlib.in_toto_run`, which returns a Metablock object containing a Link
    object.

    If a link command returns non-zero the verification is aborted.

  <Arguments>
    layout:
            A Layout object which is used to extract the Inspections.

  <Exceptions>
    Calls function that raises BadReturnValueError if an inspection returned
    non-int or non-zero.

  <Returns>
    A dictionary of metadata about the executed inspections, e.g.:

    {
      <inspection name> : {
        <Metablock containing a Link object>,
        ...
      }, ...
    }

  """
  inspection_links_dict = {}
  for inspection in layout.inspect:
    log.info("Executing command for inspection '{}'...".format(
        inspection.name))

    # FIXME: We don't want to use the base path for runlib so we patch this
    # for now. This will not stay!
    base_path_backup = in_toto.settings.ARTIFACT_BASE_PATH
    in_toto.settings.ARTIFACT_BASE_PATH = None

    # FIXME: What should we record as material/product?
    # Is the current directory a sensible default? In general?
    # If so, we should probably make it a default in run_link
    # We could use artifact rule paths.
    material_list = product_list = ["."]
    link = in_toto.runlib.in_toto_run(inspection.name, material_list,
        product_list, inspection.run)

    _raise_on_bad_retval(link.signed.byproducts.get("return-value"), inspection.run)

    inspection_links_dict[inspection.name] = link

    # Dump the inspection link file for auditing
    # Keep in mind that this pollutes the verifier's (client's) filesystem.
    filename = FILENAME_FORMAT_SHORT.format(step_name=inspection.name)
    link.dump(filename)

    in_toto.settings.ARTIFACT_BASE_PATH = base_path_backup

  return inspection_links_dict


def verify_layout_expiration(layout):
  """
  <Purpose>
    Raises an exception if the passed layout has expired, i.e. if its
    `expires` property is lesser "now".
    Time zone aware datetime objects in UTC+00:00 (Zulu Time) are used.

  <Arguments>
    layout:
            The Layout object to be verified.

  <Exceptions>
    LayoutExpiredError
    TBA (see https://github.com/in-toto/in-toto/issues/6)

  <Side Effects>
    None.

  """
  expire_datetime = iso8601.parse_date(layout.expires)
  if expire_datetime < datetime.datetime.now(tz.tzutc()):
    raise LayoutExpiredError("Layout expired")


def substitute_parameters(layout, parameter_dictionary):
  """
  <Purpose>
    This function is a transitionary measure for parameter substitution (or
    any other solution defined by the in-toto team). As of now, it acts as
    a very simple replacement layer for python-like parameters

  <Arguments>
    layout:
            The Layout object to process.

      parameter_dictionary:
            A dictionary containing key-value pairs for substitution.

  <Exceptions>
    securesystemslib.exceptions.FormatError:
      if the parameter dictionary is malformed.

    KeyError:
      if one of the keys in the parameter dictionary are not present for
      substitution

  <Side Effects>
    The layout object will have any tags replaced with the corresponding
    values defined in the parameter dictionary.
  """
  in_toto.formats.PARAMETER_DICTIONARY_SCHEMA.check_match(parameter_dictionary)

  for step in layout.steps:

    new_material_rules = []
    for rule in step.expected_materials:
      new_rule = []
      for stanza in rule:
        new_rule.append(stanza.format(**parameter_dictionary))
      new_material_rules.append(new_rule)

    new_product_rules = []
    for rule in step.expected_products:
      new_rule = []
      for stanza in rule:
        new_rule.append(stanza.format(**parameter_dictionary))
      new_product_rules.append(new_rule)

    new_expected_command = []
    for argv in step.expected_command:
      new_expected_command.append(argv.format(**parameter_dictionary))

    step.expected_command = new_expected_command
    step.expected_materials = new_material_rules
    step.expected_products = new_product_rules

  for inspection in layout.inspect:
    new_material_rules = []
    for rule in inspection.expected_materials:
      new_rule = []
      for stanza in rule:
        new_rule.append(stanza.format(**parameter_dictionary))
      new_material_rules.append(new_rule)

    new_product_rules = []
    for rule in inspection.expected_products:
      new_rule = []
      for stanza in rule:
        new_rule.append(stanza.format(**parameter_dictionary))
      new_product_rules.append(new_rule)

    new_run = []
    for argv in inspection.run:
      new_run.append(argv.format(**parameter_dictionary))

    inspection.run = new_run
    inspection.expected_materials = new_material_rules
    inspection.expected_products = new_product_rules



def verify_layout_signatures(layout_metablock, keys_dict):
  """
  <Purpose>
    Iteratively verifies the signatures of a Metablock object containing
    a Layout object for every verification key in the passed keys dictionary.

    Requires at least one key to be passed and requires every passed key to
    find a valid signature.

  <Arguments>
    layout_metablock:
            A Metablock object containing a Layout whose signatures are
            verified.

    keys_dict:
            A dictionary of keys to verify the signatures conformant with
            securesystemslib.formats.ANY_VERIFICATION_KEY_DICT_SCHEMA.

  <Exceptions>
    securesystemslib.exceptions.FormatError
      if the passed key dict does not match ANY_VERIFICATION_KEY_DICT_SCHEMA.

    SignatureVerificationError
      if the any empty verification key dictionary was passed, or
      if any of the passed verification keys fails to verify a signature.

  """
  in_toto.formats.ANY_VERIFICATION_KEY_DICT_SCHEMA.check_match(keys_dict)

  # Fail if an empty verification key dictionary was passed
  if len(keys_dict) < 1:
    raise SignatureVerificationError("Layout signature verification"
        " requires at least one key.")

  # Fail if any of the passed keys can't verify a signature on the Layout
  for junk, verify_key in six.iteritems(keys_dict):
    layout_metablock.verify_signature(verify_key)


def verify_link_signature_thresholds(layout, chain_link_dict):
  """
  <Purpose>
    Verify that for each step of the layout there are at least `threshold`
    links, signed by different authorized functionaries and return the chain
    link dictionary containing only authorized links whose signatures
    were successfully verified.

    NOTE: If the layout's key store (`layout.keys`) lists a (master) key `K`,
    with a subkey `K'`, then `K'` is authorized implicitly, to sign any link
    that `K` is authorized to sign. In other words, the trust in a master key
    extends to the trust in a subkey. The inverse is not true.

  <Arguments>
    layout:
            A Layout object whose Steps are extracted and verified.

    chain_link_dict:
            A dictionary containing link metadata per functionary per step,
            e.g.:
            {
              <link name> : {
                <functionary key id> : <Metablock containing a Link or Layout
                                        object>,
                ...
              }, ...
            }

  <Exceptions>
    ThresholdVerificationError
            If any of the steps of the passed layout does not have enough
            (`step.threshold`) links signed by different authorized
            functionaries.

  <Returns>
    A chain_link_dict containing only links with valid signatures created by
    authorized functionaries.

  """
  # Create an inverse keys-subkeys dictionary, with subkey keyids as
  # dictionary keys and main keys as dictionary values. This will be
  # required below to assess main-subkey trust delegations.
  # We assume that a given subkey can only belong to one master key
  # TODO: Is this a safe assumption? Should we assert for it?
  main_keys_for_subkeys = {}
  for main_key in list(layout.keys.values()):
    for sub_keyid in main_key.get("subkeys", []):
      main_keys_for_subkeys[sub_keyid] = main_key

  # Dict for valid and authorized links of all steps of the layout
  verfied_chain_link_dict = {}

  # For each step of the layout check the signatures of corresponding links.
  # Consider only links where the signature is valid and keys are authorized,
  # and discard others.
  # Only count one of multiple links signed with different subkeys of a main
  # key towards link threshold.
  # Only proceed with final product verification if threshold requirements are
  # fulfilled.
  for step in layout.steps:
    # Dict for valid and authorized links of a given step
    verified_key_link_dict = {}
    # List of used keyids
    used_main_keyids = []

    # Do per step link threshold verification
    for link_keyid, link in six.iteritems(chain_link_dict.get(step.name, {})):
      # Iterate over authorized keyids to find a key or subkey corresponding
      # to the given link and check if the link's keyid is authorized.
      # Subkeys of authorized main keys are authorized implicitly.
      for authorized_keyid in step.pubkeys:

        authorized_key = layout.keys.get(authorized_keyid)
        main_key_for_subkey = main_keys_for_subkeys.get(authorized_keyid)

        # The signing key is authorized
        if authorized_key and link_keyid == authorized_keyid:
          verification_key = authorized_key
          break

        # The signing key is an authorized subkey
        elif main_key_for_subkey and link_keyid == authorized_keyid:
          verification_key = main_key_for_subkey
          break

        # The signing key is a subkey of an authorized key
        elif (authorized_key and
            link_keyid in authorized_key.get("subkeys", {}).keys()):
          verification_key = authorized_key
          break

      else:
        log.info("Skipping link. Keyid '{0}' is not authorized to sign links"
            " for step '{1}'".format(link_keyid, step.name))
        continue

      # Verify signature and skip invalidly signed links
      try:
        link.verify_signature(verification_key)

      except SignatureVerificationError:
        log.info("Skipping link. Broken link signature with keyid '{0}'"
            " for step '{1}'".format(link_keyid, step.name))
        continue

      # Warn if there are links signed by different subkeys of same main key
      if verification_key["keyid"] in used_main_keyids:
        log.warning("Found links signed by different subkeys of the same main"
            " key '{}' for step '{}'. Only one of them is counted towards the"
            " step threshold.".format(verification_key["keyid"], step.name))

      used_main_keyids.append(verification_key["keyid"])

      # Keep only links with valid and authorized signature
      verified_key_link_dict[link_keyid] = link

    # For each step, verify that we have enough validly signed links from
    # distinct authorized functionaries. Links signed by different subkeys of
    # the same main key are counted only once towards the threshold.
    valid_authorized_links_cnt = (len(verified_key_link_dict) -
        (len(used_main_keyids) - len(set(used_main_keyids))))
    # TODO: To guarantee that links are signed by different functionaries
    # we rely on the layout to not carry duplicate verification keys under
    # different dictionary keys, e.g. {keyid1: KEY1, keyid2: KEY1}
    # Maybe we should add such a check to the layout validation? Or here?
    if valid_authorized_links_cnt < step.threshold:
      raise ThresholdVerificationError("Step '{}' requires at least '{}' links"
          " validly signed by different authorized functionaries. Only"
          " found '{}'".format(step.name, step.threshold,
          valid_authorized_links_cnt))

    # Add all good links of this step to the dictionary of links of all steps
    verfied_chain_link_dict[step.name] = verified_key_link_dict

  # Threshold verification succeeded, return valid and authorized links for
  # further verification
  return verfied_chain_link_dict

def verify_command_alignment(command, expected_command):
  """
  <Purpose>
    Checks if a run command aligns with an expected command. The commands align
    if all of their elements are equal. If alignment fails, a warning is
    printed.

    Note:
      Command alignment is a weak guarantee. Because a functionary can easily
      alias commands.

  <Arguments>
    command:
            A command list, e.g. ["vi", "foo.py"]
    expected_command:
            A command list, e.g. ["make", "install"]

  <Exceptions>
    None.

  <Side Effects>
    Logs warning in case commands do not align.

  """
  # In what case command alignment should fail and how that failure should be
  # propagated has been thoughly discussed in:
  # https://github.com/in-toto/in-toto/issues/46 and
  # https://github.com/in-toto/in-toto/pull/47
  # We chose the simplest solution for now, i.e. Warn if they do not align.
  if command != expected_command:
    log.warning("Run command '{0}' differs from expected command '{1}'"
        .format(command, expected_command))


def verify_all_steps_command_alignment(layout, chain_link_dict):
  """
  <Purpose>
    Iteratively checks if all expected commands as defined in the
    Steps of a Layout align with the actual commands as recorded in the Link
    metadata.

  <Arguments>
    layout:
            A Layout object to extract the expected commands from.

    chain_link_dict:
            A dictionary containing link metadata per functionary per step,
            e.g.:
            {
              <link name> : {
                <functionary key id> : <Metablock containing a Link object>,
                ...
              }, ...
            }

  <Exceptions>
    None.

  <Side Effects>
    None.

  """
  for step in layout.steps:
    # Find the according link for this step
    expected_command = step.expected_command
    key_link_dict = chain_link_dict[step.name]

    # FIXME: I think we could do this for one link per step only
    # providing that we verify command alignment AFTER threshold equality
    for keyid, link in six.iteritems(key_link_dict):
      log.info("Verifying command alignment for '{0}'...".format(
          in_toto.models.link.FILENAME_FORMAT.format(step_name=step.name,
              keyid=keyid)))

      command = link.signed.command
      verify_command_alignment(command, expected_command)


def verify_match_rule(rule_data, artifacts_queue, source_artifacts, links):
  """
  <Purpose>
    Filters artifacts from artifact queue using rule pattern and optional rule
    source prefix and consumes them if there is a corresponding destination
    artifact, filtered using the same rule pattern and an optional rule
    destination prefix, and source and destination artifacts have matching
    hashes.

    NOTE: The destination artifacts are extracted from the links dictionary,
    using destination name and destination type from the rule data. The source
    artifacts could also be extracted from the links dictionary, but would
    require the caller to pass source name and source type, as those are not
    encoded in the rule. However, we choose to let the caller directly pass the
    relevant artifacts.


  <Arguments>
    rule_data:
            An unpacked "MATCH" rule (see in_toto.rulelib).

    artifacts_queue:
            Not yet consumed artifacts (paths only).


    source_artifacts:
            All artifacts of the source item (including hashes).

    links:
            A dictionary containing link metadata per step or inspection, e.g.:
            {
              <link name> : <Metablock containing a link object>,
              ...
            }

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    The set of consumed artifacts (paths only).

  """
  consumed = set()

  # The rule can only consume artifacts if the destination link exists
  dest_link = links.get(rule_data["dest_name"])
  if not dest_link:
    return consumed

  # Extract destination artifacts from destination link
  dest_artifacts = getattr(dest_link.signed, rule_data["dest_type"])

  # Filter part 1 - Filter artifacts using optional source prefix, and subtract
  # prefix before filtering with rule pattern (see filter part 2) to prevent
  # globbing in the prefix.
  if rule_data["source_prefix"]:
    filtered_source_paths = []
    # Add trailing slash to source prefix if it does not exist
    normalized_source_prefix = os.path.join(
        rule_data["source_prefix"], "").replace("\\", "/")

    for artifact_path in artifacts_queue:
      if artifact_path.startswith(normalized_source_prefix):
        filtered_source_paths.append(
            artifact_path[len(normalized_source_prefix):])

  else:
    filtered_source_paths = artifacts_queue

  # Filter part 2 - glob above filtered artifact paths
  filtered_source_paths = fnmatch.filter(
      filtered_source_paths, rule_data["pattern"])

  # Iterate over filtered source paths and try to match the corresponding
  # source artifact hash with the corresponding destination artifact hash
  for path in filtered_source_paths:
    # If a source prefix was specified, we subtracted the prefix above before
    # globbing. We have to re-prepend the prefix in order to retrieve the
    # corresponding source artifact below.
    if rule_data["source_prefix"]:
      full_source_path = os.path.join(
          rule_data["source_prefix"], path).replace("\\", "/")

    else:
      full_source_path = path

    # If a destination prefix was specified, the destination artifact should
    # be queried with the full destination path, i.e. the prefix joined with
    # the globbed path.
    if rule_data["dest_prefix"]:
      full_dest_path = os.path.join(
          rule_data["dest_prefix"], path).replace("\\", "/")

    else:
      full_dest_path = path

    # Extract source artifact hash dict
    # We know the source artifact is available, it is also in the queue
    source_artifact = source_artifacts[full_source_path]

    # Don't consume source artifact w/o corresponding dest artifact (by path)
    try:
      dest_artifact = dest_artifacts[full_dest_path]
    except KeyError:
      continue

    # Don't consume source artifact w/o corresponding dest artifact (by hash)
    if source_artifact != dest_artifact:
      continue

    # Source and destination matched, consume artifact
    consumed.add(full_source_path)

  return consumed


def verify_create_rule(rule_pattern, artifacts_queue, materials, products):
  """
  <Purpose>
    Filters artifacts from artifacts queue using rule pattern and consumes them
    if they are not in the materials set but are in the products set, i.e.
    were created.

  <Arguments>
    rule_pattern:
            A "CREATE" rule pattern (see in_toto.rulelib).

    artifacts_queue:
            Not yet consumed artifacts (paths only).

    materials:
            All materials of an item (paths only).

    products:
            All products of an item (paths only).

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    The set of consumed artifacts (paths only).

  """
  # Filter queued artifacts using the rule pattern
  filtered_artifacts = fnmatch.filter(artifacts_queue, rule_pattern)

  # Consume filtered artifacts that are products but not materials
  consumed = set(filtered_artifacts) & (products - materials)

  return consumed


def verify_delete_rule(rule_pattern, artifacts_queue, materials, products):
  """
  <Purpose>
    Filters artifacts from artifacts queue using rule pattern and consumes them
    if they are in the materials set but are not in the products set, i.e.
    were deleted.

  <Arguments>
    rule_pattern:
            A "DELETE" rule pattern (see in_toto.rulelib).

    artifacts_queue:
            Not yet consumed artifacts (paths only).

    materials:
            All materials of an item (paths only).

    products:
            All products of an item (paths only).

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    The set of consumed artifacts (paths only).

  """
  # Filter queued artifacts using the rule pattern
  filtered_artifacts = fnmatch.filter(artifacts_queue, rule_pattern)

  # Consume filtered artifacts that are materials but not products
  consumed = set(filtered_artifacts) & (materials - products)

  return consumed


def verify_modify_rule(rule_pattern, artifacts_queue, materials, products):
  """
  <Purpose>
    Filters artifacts from artifacts queue using rule pattern and consumes them
    if they are in both the materials dict and in the products doct, but have
    different hashes, i.e. were modified.

  <Arguments>
    rule_pattern:
            A "MODIFY" rule pattern (see in_toto.rulelib).

    artifacts_queue:
            Not yet consumed artifacts (paths only).

    materials:
            All materials of an item (including hashes).

    products:
            All products of an item (including hashes).

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    The set of consumed artifacts (paths only).

  """
  # Filter queued artifacts using the rule pattern
  filtered_artifacts = fnmatch.filter(artifacts_queue, rule_pattern)

  # Filter filtered artifacts that are materials and products
  filtered_artifacts = set(filtered_artifacts) & \
      set(materials.keys()) & set(products.keys())

  # Consume filtered artifacts that have different hashes
  consumed = set()
  for path in filtered_artifacts:
    if materials[path] != products[path]:
      consumed.add(path)

  return consumed


def verify_allow_rule(rule_pattern, artifacts_queue):
  """
  <Purpose>
    Consumes artifacts, filtered from the artifacts queue using rule pattern.

  <Arguments>
    rule_pattern:
            An "ALLOW" rule pattern (see in_toto.rulelib).

    artifacts_queue:
            Not yet consumed artifacts (paths only).

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    The set of consumed artifacts (paths only).

  """
  # Filter queued artifacts using the rule pattern
  filtered_artifacts = fnmatch.filter(artifacts_queue, rule_pattern)

  # Consume all filtered artifacts
  return set(filtered_artifacts)


def verify_disallow_rule(rule_pattern, artifacts_queue):
  """
  <Purpose>
    Raises RuleVerificationError if rule pattern applies to any artifacts in
    the queue.

    NOTE: Each set of rules should have a terminal DISALLOW rule to make
    overall verification fail in case preceding rules did not consume all
    artifacts as intended.

  <Arguments>
    rule_pattern:
            A "DISALLOW" rule pattern (see in_toto.rulelib).

    artifacts_queue:
            Not yet consumed artifacts (paths only).

  <Exceptions>
    RuleVerificationError
        if the rule pattern filters artifacts in the artifact queue.

  <Side Effects>
    None.

  <Returns>
    None.

  """
  filtered_artifacts = fnmatch.filter(artifacts_queue, rule_pattern)

  if len(filtered_artifacts):
    raise RuleVerificationError("'DISALLOW {}' matched the following "
      "artifacts: {}\n{}".format(rule_pattern, filtered_artifacts,
      _get_artifact_rule_traceback()))


def _get_artifact_rule_traceback():
  """Build and return string form global `RULE_TRACE` which may be used as
  error message for RuleVerificationError.

  """
  traceback_str = "Full trace for 'expected_{0}' of item '{1}':\n".format(
      RULE_TRACE["source_type"], RULE_TRACE["source_name"])

  # Show all materials and products available in the beginning and
  # label the one that is used to generate a queue.
  for source_type in ["materials", "products"]:
    traceback_str += "Available {}{}:\n{}\n".format(
        source_type,
        [" (used for queue)", ""][RULE_TRACE["source_type"] != source_type],
        RULE_TRACE[source_type])

  for trace_entry in RULE_TRACE["trace"]:
    traceback_str += "Queue after '{0}':\n".format(
        " ".join(trace_entry["rule"]))
    traceback_str += "{}\n".format(trace_entry["queue"])

  return traceback_str


def verify_item_rules(source_name, source_type, rules, links):
  """
  <Purpose>
    Apply all passed material or product rules (see source_type) of a given
    step or inspection (see source_name), to enforce and authorize the
    corresponding artifacts and to guarantee that artifacts are linked together
    across steps of the supply chain.

    The mode of operation is similar to that of a firewall:
    In the beginning all materials or products of the step or inspection are
    placed into an artifact queue. The rules are then applied sequentially,
    consuming artifacts in the queue, i.e. removing them from the queue, on
    success.
    The only exception is the "DISALLOW" rule. It does not consume artifacts
    but instead raises a RuleVerificationError if its pattern matches any
    artifacts in the queue.
    Thus, each set of rules should have a terminal "DISALLOW" rule in order
    to be effective.


  <Arguments>
    source_name:
            The name of the item (step or inspection) being verified.

    source_type:
            One of "materials" or "products" depending on whether the rules are
            taken from the "expected_materials" or "expected_products" field of
            the item being verified.

    rules:
            The list of rules (material or product rules) for the item being
            verified.

    links:
            A dictionary containing link metadata per step or inspection, e.g.:
            {
              <link name> : <Metablock containing a link>,
              ...
            }

  <Exceptions>
    FormatError
        if source_type is not "materials" or "products", or
        if a rule in the passed list of rules does not conform with any rule
        format.

    RuleVerificationError
        if a DISALLOW rule matches any artifacts in the corresponding artifact
        queue.

  <Side Effects>
    Clears and populates the global RULE_TRACE data structure.

  """
  if source_type not in ["materials", "products"]:
    raise securesystemslib.exceptions.FormatError(
        "Argument 'source_type' of function 'verify_item_rules' has to be "
        "one of 'materials' or 'products'. Got: '{}'".format(source_type))

  # Create shortcuts to item's materials and products (including hashes),
  # required to verify "modify" and "match" rules.
  materials_dict = links[source_name].signed.materials
  products_dict = links[source_name].signed.products

  # All other rules only require materials or products paths (without hashes)
  materials_paths = set(materials_dict.keys())
  products_paths = set(products_dict.keys())

  # Depending on the source type we create the artifact queue from the item's
  # materials or products and use it to keep track of (not) consumed artifacts.
  # The queue also only contains aritfact keys (without hashes)
  artifacts = getattr(links[source_name].signed, source_type)
  artifacts_queue = set(artifacts.keys())

  # Reset and re-populate rule traceback info dict for a rich error message
  RULE_TRACE.clear()
  RULE_TRACE["source_name"] = source_name
  RULE_TRACE["source_type"] = source_type
  RULE_TRACE["materials"] = list(materials_dict)
  RULE_TRACE["products"] = list(products_dict)
  RULE_TRACE["trace"] = []

  # Process rules and remove consumed items from queue in each iteration
  for rule in rules:
    log.info("Verifying '{}'...".format(" ".join(rule)))

    # Parse the rule and create two shortcuts to contained rule data
    rule_data = in_toto.rulelib.unpack_rule(rule)
    _type = rule_data["rule_type"]
    _pattern = rule_data["pattern"]

    # All rules except "disallow" consume artifacts in the queue
    if _type == "match":
      consumed = verify_match_rule(
          rule_data, artifacts_queue, artifacts, links)

    elif _type == "create":
      consumed = verify_create_rule(
          _pattern, artifacts_queue, materials_paths, products_paths)

    elif _type == "delete":
      consumed = verify_delete_rule(
          _pattern, artifacts_queue, materials_paths, products_paths)

    elif _type == "modify":
      consumed = verify_modify_rule(
          _pattern, artifacts_queue, materials_dict, products_dict)

    elif _type == "allow":
      consumed = verify_allow_rule(_pattern, artifacts_queue)

    # It's up to the "disallow" rule to raise an error if artifacts were not
    # consumed as intended
    elif _type == "disallow":
      verify_disallow_rule(_pattern, artifacts_queue)

    else: # pragma: no cover (unreachable)
      raise securesystemslib.exceptions.FormatError(
          "Invaldid rule type '{}'.".format(_type))

    artifacts_queue -= consumed

    # Append rule and copy of queue to global info for a rich error message
    RULE_TRACE["trace"].append({
          "rule": rule,
          "queue": list(artifacts_queue)
        })


def verify_all_item_rules(items, links):
  """
  <Purpose>
    Iteratively verifies artifact rules of passed items (Steps or Inspections).

  <Arguments>
    items:
            A list containing Step or Inspection objects whose material
            and product rules will be verified.

    links:
            A dictionary containing link metadata per step or inspection, e.g.:
            {
              <link name> : <Metablock containing a Link object>,
              ...
            }

  <Exceptions>
    None.

  <Side Effects>
    None.

  """
  for item in items:
    log.info("Verifying material rules for '{}'...".format(item.name))
    verify_item_rules(item.name, "materials", item.expected_materials, links)

    log.info("Verifying product rules for '{}'...".format(item.name))
    verify_item_rules(item.name, "products", item.expected_products, links)


def verify_threshold_constraints(layout, chain_link_dict):
  """
  <Purpose>
    Verifies that all links corresponding to a given step report the same
    materials and products.

    NOTE: This function does not verify if the signatures of each link
    corresponding to a step are valid or created by a different authorized
    functionary. This should be done earlier, using the function
    `verify_link_signature_thresholds`.

  <Arguments>
    layout:
            The layout whose step thresholds are being verified

    chain_link_dict:
            A dictionary containing link metadata per functionary per step,
            e.g.:
            {
              <link name> : {
                <functionary key id> : <Metablock containing a Link object>,
                ...
              }, ...
            }

  <Exceptions>
    ThresholdVerificationError
        If there are not enough (threshold) links for a steps

        If the artifacts for all links of a step are not equal


  <Side Effects>
    None.

  """

  # We are only interested in links that are related to steps defined in the
  # Layout, so iterate over layout.steps
  for step in layout.steps:
    # Skip steps that don't require multiple functionaries
    if step.threshold <= 1:
      log.info("Skipping threshold verification for step '{0}' with"
          " threshold '{1}'...".format(step.name, step.threshold))
      continue

    log.info("Verifying threshold for step '{0}' with"
        " threshold '{1}'...".format(step.name, step.threshold))
    # Extract the key_link_dict for this step from the passed chain_link_dict
    key_link_dict = chain_link_dict[step.name]

    # Check if we have at least <threshold> links for this step
    # NOTE: This is already done in `verify_link_signature_thresholds`,
    # Should we remove the check?
    if len(key_link_dict) < step.threshold:
      raise ThresholdVerificationError("Step '{0}' not performed"
          " by enough functionaries!".format(step.name))

    # Take a reference link (e.g. the first in the step_link_dict)
    reference_keyid = list(key_link_dict.keys())[0]
    reference_link = key_link_dict[reference_keyid]

    # Iterate over all links to compare their properties with a reference_link
    for keyid, link in six.iteritems(key_link_dict):
      # TODO: Do we only care for artifacts, or do we want to
      # assert equality of other properties as well?
      if (reference_link.signed.materials != link.signed.materials or
          reference_link.signed.products != link.signed.products):
        raise ThresholdVerificationError("Links '{0}' and '{1}' have different"
            " artifacts!".format(
                in_toto.models.link.FILENAME_FORMAT.format(
                    step_name=step.name, keyid=reference_keyid),
                in_toto.models.link.FILENAME_FORMAT.format(
                    step_name=step.name, keyid=keyid)))


def reduce_chain_links(chain_link_dict):
  """
  <Purpose>
    Iterates through the passed chain_link_dict and builds a dict with
    step-name as keys and link objects as values.
    We already check if the links of different functionaries are
    identical.

  <Arguments>
    layout:
            The layout specified by the project owner against which the
            threshold will be verified.

    chain_link_dict:
            A dictionary containing link metadata per functionary per step,
            e.g.:
            {
              <link name> : {
                <functionary key id> : <Metablock containing a Link object>,
                ...
              }, ...
            }

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    A dictionary containing one Link metadata object per step only if
    the link artifacts of all link objects are identical for a step.

  """

  reduced_chain_link_dict = {}

  for step_name, key_link_dict in six.iteritems(chain_link_dict):
    # Extract the key_link_dict for this step from the passed chain_link_dict
    # take one exemplary link (e.g. the first in the step_link_dict)
    # form the reduced_chain_link_dict to return
    reduced_chain_link_dict[step_name] = list(key_link_dict.values())[0]

  return reduced_chain_link_dict


def verify_sublayouts(layout, chain_link_dict, superlayout_link_dir_path):
  """
  <Purpose>
    Checks if any step has been delegated by the functionary, recurses into
    the delegation and replaces the layout object in the chain_link_dict
    by an equivalent link object.

  <Arguments>
    layout:
            The layout specified by the project owner.

    chain_link_dict:
            A dictionary containing link metadata per functionary per step,
            e.g.:
            {
              <link name> : {
                <functionary key id> : <Metablock containing a Link or Layout
                                          object>,
                ...
              }, ...
            }

    superlayout_link_dir_path:
            A path to a directory, where links of the superlayout are loaded
            from. Links of the sublayout are expected to be in a subdirectory
            relative to this path, with a name in the format
            in_toto.models.layout.SUBLAYOUT_LINK_DIR_FORMAT.

  <Exceptions>
    raises an Exception if verification of the delegated step fails.

  <Side Effects>
    None.

  <Returns>
    The passed dictionary containing link metadata per functionary per step,
    with layouts replaced with summary links.
    e.g.:
    {
      <link name> : {
        <functionary key id> : <Metablock containing a Link object>,
        ...
      }, ...
    }

  """
  for step_name, key_link_dict in six.iteritems(chain_link_dict):

    for keyid, link in six.iteritems(key_link_dict):

      if link.type_ == "layout":
        log.info("Verifying sublayout {}...".format(step_name))
        layout_key_dict = {}

        # Retrieve the entire key object for the keyid
        # corresponding to the link
        layout_key_dict = {keyid: layout.keys.get(keyid)}

        # Sublayout links are expected to be in a directory with the following
        # name relative the the current link directory path, i.e. if there
        # are multiple levels of sublayout nesting, the links are expected to
        # be nested accordingly
        sublayout_link_dir = SUBLAYOUT_LINK_DIR_FORMAT.format(
            name=step_name, keyid=keyid)

        sublayout_link_dir_path = os.path.join(
            superlayout_link_dir_path, sublayout_link_dir)

        # Make a recursive call to in_toto_verify with the
        # layout and the extracted key object
        summary_link = in_toto_verify(link, layout_key_dict,
            link_dir_path=sublayout_link_dir_path, step_name=step_name)

        # Replace the layout object in the passed chain_link_dict
        # with the link file returned by in-toto-verify
        key_link_dict[keyid] = summary_link

  return chain_link_dict


def get_summary_link(layout, reduced_chain_link_dict, name):
  """
  <Purpose>
    Merges the materials of the first step (as mentioned in the layout)
    and the products of the last step and returns a new link.
    This link reports the materials and products and summarizes the
    overall software supply chain.
    NOTE: The assumption is that the steps mentioned in the layout are
    to be performed sequentially. So, the first step mentioned in the
    layout denotes what comes into the supply chain and the last step
    denotes what goes out.

  <Arguments>
    layout:
            The layout specified by the project owner.

    reduced_chain_link_dict:
            A dictionary containing link metadata per step,
            e.g.:
            {
              <link name> : <Metablock containing a Link object>,
              ...
            }
    name:
            The name that the summary link will be associated with.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    A Metablock object containing a Link which summarizes the materials and
    products of the overall software supply chain.

  """
  # Create empty link object
  summary_link = in_toto.models.link.Link()

  # Take first and last link in the order the corresponding
  # steps appear in the layout, if there are any.
  if len(layout.steps) > 0:
    first_step_link = reduced_chain_link_dict[layout.steps[0].name]
    last_step_link = reduced_chain_link_dict[layout.steps[-1].name]

    summary_link.materials = first_step_link.signed.materials
    summary_link.name = name

    summary_link.products = last_step_link.signed.products
    summary_link.byproducts = last_step_link.signed.byproducts
    summary_link.command = last_step_link.signed.command

  return Metablock(signed=summary_link)


def in_toto_verify(layout, layout_key_dict, link_dir_path=".",
    substitution_parameters=None, step_name=""):
  """
  <Purpose>
    Does entire in-toto supply chain verification of a final product
    by performing the following actions:

        1.  Verify layout signature(s), requires at least one verification key
            to be passed, and a valid signature for each passed key.

        2.  Verify layout expiration


        3.  Load link metadata for every Step defined in the layout and
            fail if less links than the defined threshold for a step are found.
            NOTE: Link files are expected to have the corresponding step
            and the functionary, who carried out the step, encoded in their
            filename.

        4.  Verify functionary signature for every loaded Link, skipping links
            with failing signatures or signed by unauthorized functionaries,
            and fail if less than `threshold` links validly signed by different
            authorized functionaries can be found.
            The routine returns a dictionary containing only links with valid
            signatures by authorized functionaries.

        5.  Verify sublayouts
            Recurses into layout verification for each link of the
            superlayout that is a layout itself (i.e. sublayout).
            Links for the sublayout are expected to be in a subdirectory
            relative to the superlayout's link_dir_path, with a name in the
            format: in_toto.models.layout.SUBLAYOUT_LINK_DIR_FORMAT.

            The successfully verified sublayout is replaced with an unsigned
            summary link in the chain_link_dict of the superlayout.
            The summary link is then used just like a regular link
            to verify command alignments, thresholds and inspections according
            to the superlayout.

        6.  Verify alignment of defined (Step) and reported (Link) commands
            NOTE: Won't raise exception on mismatch

        7.  Verify threshold constraints, i.e. if all links corresponding to
            one step have recorded the same artifacts (materials and products).

        8.  Verify rules defined in each Step's expected_materials and
            expected_products field
            NOTE: At this point no Inspection link metadata is available,
            hence (MATCH) rules cannot reference materials or products of
            Inspections.
            Verifying Steps' artifact rules before executing Inspections
            guarantees that Inspection commands don't run on compromised
            target files, which would be a surface for attacks.

        9.  Execute Inspection commands
            NOTE: Inspections, similar to Steps executed with 'in-toto-run',
            will record materials before and products after command execution.
            For now it records everything in the current working directory.

        10. Verify rules defined in each Inspection's expected_materials and
            expected_products field

  <Arguments>
    layout:
            Layout object that is being verified.

    layout_key_dict:
            Dictionary of project owner public keys, used to verify the
            layout's signature.

    link_dir_path: (optional)
            A path to the directory from which link metadata files
            corresponding to the steps in the passed layout are loaded.
            Default is the current working directory.

    substitution_parameters: (optional)
            a dictionary containing key-value pairs for substituting in the 
            following metadata fields:

              - artifact rules in step and inspection definitions in the layout
              - the run fields in the inspection definitions
              - the expected command in the step definitions
    step_name: (optional)
            The step that the layout corresponds to, typically used during
            recursive calls of in_toto_verify. This usually happens when
            resolving sublayouts. The function verify_sublayouts may provide a
            clearer picture on how it's used.

  <Exceptions>
    None.

  <Side Effects>
    Read link metadata files from disk

  <Returns>
    A link which summarizes the materials and products of the overall
    software supply chain (used by super-layout verification if any)

  """
  log.info("Verifying layout signatures...")
  verify_layout_signatures(layout, layout_key_dict)

  # For the rest of the verification we only care about the layout payload
  # (Layout) that carries all the information and not about the layout
  # container (Metablock) that also carries the signatures
  layout = layout.signed

  log.info("Verifying layout expiration...")
  verify_layout_expiration(layout)

  # If there are parameters sent to the tanslation layer, substitute them
  if substitution_parameters is not None:
    log.info('Performing parameter substitution...')
    substitute_parameters(layout, substitution_parameters)

  log.info("Reading link metadata files...")
  chain_link_dict = load_links_for_layout(layout, link_dir_path)

  log.info("Verifying link metadata signatures...")
  chain_link_dict = verify_link_signature_thresholds(layout, chain_link_dict)

  log.info("Verifying sublayouts...")
  chain_link_dict = verify_sublayouts(layout, chain_link_dict, link_dir_path)

  log.info("Verifying alignment of reported commands...")
  verify_all_steps_command_alignment(layout, chain_link_dict)

  log.info("Verifying threshold constraints...")
  verify_threshold_constraints(layout, chain_link_dict)
  reduced_chain_link_dict = reduce_chain_links(chain_link_dict)

  log.info("Verifying Step rules...")
  verify_all_item_rules(layout.steps, reduced_chain_link_dict)

  log.info("Executing Inspection commands...")
  inspection_link_dict = run_all_inspections(layout)

  log.info("Verifying Inspection rules...")
  # Artifact rules for inspections can reference links that correspond to
  # Steps or Inspections, hence the concatenation of both collections of links
  combined_links = reduced_chain_link_dict.copy()
  combined_links.update(inspection_link_dict)
  verify_all_item_rules(layout.inspect, combined_links)

  # We made it this far without exception that means, verification passed
  log.info("The software product passed all verification.")

  # Return a link file which summarizes the entire software supply chain
  # This is mostly relevant if the currently verified supply chain is embedded
  # in another supply chain
  return get_summary_link(layout, reduced_chain_link_dict, step_name)
