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
from in_toto.models.metadata import Metablock
from in_toto.models.link import (FILENAME_FORMAT, FILENAME_FORMAT_SHORT)
from in_toto.exceptions import (RuleVerficationError, LayoutExpiredError,
    ThresholdVerificationError, BadReturnValueError,
    SignatureVerificationError)
import in_toto.rulelib

# Inherits from in_toto base logger (c.f. in_toto.log)
log = logging.getLogger(__name__)

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


def load_links_for_layout(layout):
  """
  <Purpose>
    Try to load all existing metadata files for each Step of the Layout
    from the current directory.

    For each step the metadata might consist of multiple (thresholds) Link
    or Layout (sub-layouts) files.

  <Arguments>
    layout:
          Layout object

  <Side Effects>
    Calls function to read files from disk

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
    # FIXME: Should we really pass on IOError, or just skip inexistent links
    for keyid in step.pubkeys:
      filename = FILENAME_FORMAT.format(step_name=step.name, keyid=keyid)

      try:
        metadata = Metablock.load(filename)
        links_per_step[keyid] = metadata

      except IOError:
        pass

    # Check if the step has been performed by enough number of functionaries
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

  verfied_chain_link_dict = {}
  # Check signatures on passed links, if they are valid and authorized, but
  # don't fail yet, instead add authorized links with passing signatures
  # to a `verfied_chain_link_dict` and check later if the threshold
  # requirements are fulfilled. That is, we don't care if there are a few
  # bad links, as long as we have enough good links. Only the good links will
  # be considered for further final product verification.
  for step in layout.steps:
    # Contains all links corresponding to a step with successfully verified
    # signatures, authorized to perform the step
    verified_key_link_dict = {}

    # Iterate over links corresponding to a step
    for keyid, link in six.iteritems(chain_link_dict.get(step.name, {})):

      # Skip unauthorized links
      if keyid not in step.pubkeys:
        log.info("Skipping link. Keyid '{0}' is not authorized to sign links"
            " for step '{1}'".format(keyid, step.name))
        continue

      # Verify signature and skip invalidly signed links
      try:
        verify_key = layout.keys.get(keyid)
        link.verify_signature(verify_key)

      except SignatureVerificationError:
        log.info("Skipping link. Broken link signature with keyid '{0}'"
            " for step '{1}'".format(keyid, step.name))

      else:
        # Good link: The signature is valid and the signer was authorized
        verified_key_link_dict[keyid] = link

    # Add all good links for a step to the dictionary of links for all steps
    verfied_chain_link_dict[step.name] = verified_key_link_dict

  # For each step, verify that we have enough validly signed links signed by
  # different authorized functionaries.
  # TODO: To guarantee that links are signed by different functionaries
  # we rely on the layout to not carry duplicate verification keys under
  # different dictionary keys, e.g. {keyid1: KEY1, keyid2: KEY1}
  # Maybe we should add such a check to the layout validation? Or here?
  for step in layout.steps:
    valid_authorized_links_cnt = len(verfied_chain_link_dict[step.name])
    if valid_authorized_links_cnt < step.threshold:
      raise ThresholdVerificationError("Step requires at least '{}' links"
          " validly signed by different authorized functionaries. Only"
          " found '{}'".format(step.threshold, valid_authorized_links_cnt))

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


def verify_match_rule(rule, source_artifacts_queue, source_artifacts, links):
  """
  <Purpose>
    Verifies that for each queued source artifact filtered by the specified
    source pattern there is a destination artifact filtered by the specified
    destination pattern and they are equal in terms of path and file hash.

    This guarantees that artifacts were not modified between steps/inspections.

  <Terms>
    queued source artifacts:
        Artifacts reported by the link for the step/inspection containing passed
        rule that have not been handled by a previous rule (are still in the
        queue). If the rule was in the expected_materials list the artifacts are
        materials, if the rule was in the expected_products list the artifacts
        are products.

    destination artifacts:
        Artifacts reported by the link of the step as specified by the rule
        (... FROM <step>). The artifacts are materials or products as specified
        by the rule (... WITH (MATERIALS|PRODUCTS)).

    source pattern:
        Glob pattern specified by the rule, i.e.:
        [<source-path-prefix>] + <pattern>
        See https://docs.python.org/2/library/fnmatch.html for wildcards

    destination pattern:
        Glob pattern specified by the rule, i.e.:
        [<destination-path-prefix>] + <pattern>
        See https://docs.python.org/2/library/fnmatch.html for wildcards

    artifact equality:
        A source and destination artifact are equal if the source artifact path
        minus an optional source-path-prefix equals the destination artifact
        path minus an optional destination-path-prefix, and the hash of both
        artifacts are equal.
        The path prefixes allow for relocating the artifacts between
        steps/inspections. Path prefixes don't allow wildcards.

  <Notes>
    The rule is only applied on source artifacts filtered by the source
    pattern, i.e.: if no artifacts are found the rule always passes.

    rule: ["MATCH", "*", WITH, ...]
    source artifacts queue: [], destination artifacts: ["foo"]
    PASS (makes sense?)

    rule: ["MATCH", "foo", WITH, ...]
    source artifacts queue: ["bar"], destination artifacts: ["foo"]
    PASS (might seem strange)

  <Arguments>
    rule:
            ["MATCH", "<pattern>", ["IN", "<source-path-prefix>",]
                "WITH", ("MATERIALS"|"PRODUCTS"),
                ["IN", "<destination-path-prefix>",] "FROM" "<step>"]

    source_artifacts_queue:
            A list of artifact paths that haven't been handled by a previous
            rule of the step/inspection.

    source_artifacts:
            A dictionary of artifacts, depending on the list the rule was
            extracted from, materials or products of the step or inspection the
            rule was extracted from, with artifact paths as keys and HASHDICTS
            as values. The format is: { <path> : HASHDICT, ...}

    links:
            A dictionary containing link metadata per step or inspection, e.g.:
            {
              <link name> : <Metablock containing a Link object>,
              ...
            }

  <Exceptions>
    FormatError
        if the rule does not conform with the rule format.

    RuleVerficationError
        if the destination link is not found in the passed link dictionary.
        if the corresponding destination artifact of a filtered source artifact
        is not found.
        if a hash of a source artifact and the hash of a corresponding target
        artifact are not equal.

  <Side Effects>
    None.

  <Returns>
    A list of artifacts that were matched by the rule.

  """
  rule_data = in_toto.rulelib.unpack_rule(rule)
  dest_name = rule_data["dest_name"]
  dest_type = rule_data["dest_type"]

  # Extract destination link
  try:
    dest_link = links[dest_name]
  except KeyError:
    raise RuleVerficationError("Rule '{rule}' failed, destination link"
        " '{dest_link}' not found in link dictionary".format(
            rule=" ".join(rule), dest_link=dest_name))

  # Extract destination artifacts from destination link
  if dest_type.lower() == "materials":
    dest_artifacts = dest_link.signed.materials

  # NOTE: Can't reach `else` branch, if the source_type is none of these
  # types an exception would have been raised above in `unpack_rule`
  elif dest_type.lower() == "products": # pragma: no branch
    dest_artifacts = dest_link.signed.products

  # Filter I - take only queued paths with specified prefix and
  # subtract prefix
  # We first subtract the prefix and then apply the pattern in Filter II
  # (instead of applying prefix + pattern) to prevent globbing in the prefix
  if rule_data["source_prefix"]:
    filtered_source_paths = []
    for artifact_path in source_artifacts_queue:
      if artifact_path.startswith(rule_data["source_prefix"] + os.sep):
        filtered_source_paths.append(
            artifact_path[len(rule_data["source_prefix"] + os.sep):])
  else:
    filtered_source_paths = source_artifacts_queue

  # Filter II - apply glob pattern on remaining artifact paths
  filtered_source_paths = fnmatch.filter(
      filtered_source_paths, rule_data["pattern"])

  # Match source artifact with destination artifact
  for path in filtered_source_paths:

    # If we subtracted an optional source prefix in Filter I we have to
    # re-concatenate to find the correct keys in the source artifact dictionary
    if rule_data["source_prefix"]:
      full_source_path = rule_data["source_prefix"] + os.sep + path
    else:
      full_source_path = path

    # We have to concatenate filtered source path (without source prefix)
    # with an optional destination prefix to find the correct key in the
    # destination artifact dictionary
    if rule_data["dest_prefix"]:
      full_dest_path = rule_data["dest_prefix"] + os.sep + path
    else:
      full_dest_path = path

    # Is it okay to assume that full_source_path returns an artifact? The path
    # should not be in the queue, if it is not in the artifact dictionary
    source_artifact = source_artifacts[full_source_path]

    # Extract destination artifact from destination link
    try:
      dest_artifact = dest_artifacts[full_dest_path]
    except Exception:
      raise RuleVerficationError("Rule '{rule}' failed, destination artifact"
          " '{path}' not found in {type} of '{name}'"
              .format(rule=" ".join(rule), path=full_dest_path, name=dest_name,
                  type=dest_type))

    # Compare the hashes of source and destination artifacts
    if source_artifact != dest_artifact:
      raise RuleVerficationError("Rule '{rule}' failed, source artifact"
          " '{source}' and destination artifact '{dest}' hashes don't match."
              .format(rule=" ".join(rule), source=full_source_path,
                  dest=full_dest_path))

    # Matching went well, let's remove the path from the queue. Subsequent rules
    # won't see this artifact anymore.
    source_artifacts_queue.remove(full_source_path)

  return source_artifacts_queue


def verify_create_rule(rule, source_materials_queue, source_products_queue):
  """
  <Purpose>
    The create rule guarantees that no product filtered by the pattern, already
    appears in the materials queue, i.e. that it was created in that step.

  <Notes>
    The create rule always passes if the pattern does not match any products:

    rule: ["CREATE", "*"]
    source materials queue: ["foo"], source products queue: []
    PASS (makes sense?)

    rule: ["CREATE", "foo"]
    source materials queue: ["foo"], source products queue: []
    PASS (might seem strange)

    The CREATE rule DOES NOT verify if the artifact has appeared in previous or
    will appear in later steps of the software supply chain.

  <Arguments>
    rule:
            ["CREATE", "<path pattern>"]
            See https://docs.python.org/2/library/fnmatch.html for wildcards

    source_materials_queue:
            A list of material paths that were not matched by a previous rule.

    source_products_queue:
            A list of product paths that were not matched by a previous rule.

  <Exceptions>
    RuleVerficationError
        if a product filtered by the pattern also appears in the materials
        queue.

  <Side Effects>
    None.

  <Returns>
    The updated products queue (minus newly created artifacts).

  """
  rule_data = in_toto.rulelib.unpack_rule(rule)


  matched_products = fnmatch.filter(
      source_products_queue, rule_data["pattern"])

  for matched_product in matched_products:
    if matched_product in source_materials_queue:
      raise RuleVerficationError("Rule '{0}' failed, product '{1}' was found"
          " in materials but should have been newly created."
              .format(" ".join(rule), matched_product))

  return list(set(source_products_queue) - set(matched_products))


def verify_delete_rule(rule, source_materials_queue, source_products_queue):
  """
  <Purpose>
    The delete rule guarantees that no material filtered by the pattern also
    appears in the products queue, i.e. that it was deleted in that step.

  <Notes>
    The delete rule always passes if the pattern does not match any materials:

    rule: ["DELETE", "*"]
    source materials queue: [], source products queue: ["foo"]
    PASS (makes sense?)

    rule: ["DELETE", "foo"]
    source materials queue: [], source products queue: ["foo"]
    PASS (might seem strange)

    The delete rule DOES NOT verify if the artifact has appeared in previous or
    will appear in later steps of the software supply chain.

  <Arguments>
    rule:
            ["DELETE", "<path pattern>"]
            See https://docs.python.org/2/library/fnmatch.html for wildcards

    source_materials_queue:
            A list of material paths that were not matched by a previous rule.

    source_products_queue:
            A list of product paths that were not matched by a previous rule.

  <Exceptions>
    RuleVerficationError
        if a material filtered by the pattern also appears in the products
        queue.

  <Side Effects>
    None.

  <Returns>
    The updated materials queue (minus deleted artifacts).

  """
  rule_data = in_toto.rulelib.unpack_rule(rule)

  matched_materials = fnmatch.filter(
      source_materials_queue, rule_data["pattern"])

  for matched_material in matched_materials:
    if matched_material in source_products_queue:
      raise RuleVerficationError("Rule '{0}' failed, material '{1}' was found"
          " in products but should have been deleted."
              .format(" ".join(rule), matched_material))

  return list(set(source_materials_queue) - set(matched_materials))


def verify_modify_rule(rule, source_materials_queue, source_products_queue,
      source_materials, source_products):
  """
  <Purpose>
    The modify rule guarantees that for each material filtered by the pattern
    there is a product filtered by the pattern (and vice versa) and that their
    hashes are not equal, i.e. the artifact was modified.

  <Arguments>
    rule:
            ["MODIFY", "<path pattern>"]
            See https://docs.python.org/2/library/fnmatch.html for wildcards

    source_materials_queue:
            A list of material paths that were not matched by a previous rule.

    source_products_queue:
            A list of product paths that were not matched by a previous rule.

    source_materials:
            A dictionary of materials with artifact paths as keys and HASHDICTS
            as values. Format is: {<path> : HASHDICT}

    source_products:
            A dictionary of products with artifact paths as keys and HASHDICTS
            as values. Format is: {<path> : HASHDICT}

  <Exceptions>
    RuleVerficationError
        if the materials and products matched by the pattern are not equal in
        terms of paths.
        if any material-product pair has the same hash (was not modified).

  <Side Effects>
    None.

  <Returns>
    The updated materials and products queues (minus modified artifacts).

  """
  rule_data = in_toto.rulelib.unpack_rule(rule)

  # Filter materials and products using the pattern and create sets to
  # take advantage of Python set operations
  matched_materials = set(fnmatch.filter(
      source_materials_queue, rule_data["pattern"]))
  matched_products = set(fnmatch.filter(
      source_products_queue, rule_data["pattern"]))

  matched_materials_only = matched_materials - matched_products
  matched_products_only =  matched_products - matched_materials

  if len(matched_materials_only):
    raise RuleVerficationError("Rule '{0}' failed, the following paths appear"
        " as materials but not as products:\n\t{1}"
            .format(" ".join(rule), ", ".join(matched_materials_only)))

  if len(matched_products_only):
    raise RuleVerficationError("Rule '{0}' failed, the following paths appear"
        " as products but not as materials:\n\t{1}"
            .format(" ".join(rule), ", ".join(matched_products_only)))

  # If we haven't failed yet the two sets are equal and we can test their
  # hash in-equalities
  for path in matched_materials:
    # Is it okay to assume that path returns an artifact? The path
    # should not be in the queues, if it is not in the artifact dictionaries
    if source_materials[path] == source_products[path]:
      raise RuleVerficationError("Rule '{0}' failed, material and product '{1}'"
          " have the same hash (were not modified)."
              .format(" ".join(rule), path))

  return (list(set(source_materials_queue) - set(matched_materials)),
      list(set(source_products_queue) - set(matched_products)))


def verify_allow_rule(rule, source_artifacts_queue):
  """
  <Purpose>
    Authorizes the materials or products reported by a link metadata file
    and filtered by the specified pattern.

    The allow rule verification will never fail, but it modifies the artifact
    queue which affects the rest of the rules verification routine. See
    `verify_item_rules`.

  <Arguments>
    rule:
            ["ALLOW", "<path pattern>"]
            See https://docs.python.org/2/library/fnmatch.html for wildcards

    source_artifacts_queue:
            A list of artifact paths that were not matched by a previous rule.

  <Exceptions>
    FormatError
        if the rule does not conform with the rule format.

  <Side Effects>
    None.

  <Returns>
    The source artifact queue minus the files that were matched by the rule.

  """
  rule_data = in_toto.rulelib.unpack_rule(rule)

  matched_artifacts = fnmatch.filter(
      source_artifacts_queue, rule_data["pattern"])

  return list(set(source_artifacts_queue) - set(matched_artifacts))


def verify_disallow_rule(rule, source_artifacts_queue):
  """
  <Purpose>
    Verifies that the specified pattern does not match any materials or
    products.

  <Arguments>
    rule:
            ["DISALLOW", "<path pattern>"]
            See https://docs.python.org/2/library/fnmatch.html for wildcards

    source_artifacts_queue:
            A list of artifact paths that were not matched by a previous rule.

  <Exceptions>
    RuleVerficationError
        if path pattern matches artifacts in artifact queue.

  <Side Effects>
    None.

  <Returns>
    None.

  """
  rule_data = in_toto.rulelib.unpack_rule(rule)

  matched_artifacts = fnmatch.filter(
      source_artifacts_queue, rule_data["pattern"])

  if len(matched_artifacts):
    raise RuleVerficationError("Rule '{0}' failed, pattern matched disallowed"
        " artifacts: '{1}' ".format(" ".join(rule), matched_artifacts))


def verify_item_rules(source_name, source_type, rules, links):
  """
  <Purpose>
    Iteratively apply all passed material or product rules of one item (step or
    inspection) to enforce and authorize artifacts reported by the
    corresponding link and/or to guarantee that artifacts are linked together
    across links.
    In the beginning all artifacts are placed in a queue according to their
    type. If an artifact gets consumed by a rule it is removed from the queue,
    hence an artifact can only be consumed once.


  <Algorithm>
      1.  Create materials queue and products queue, and a generic artifacts
          queue based on the source_type (materials or products)

      2.  For each rule:
          1.  Apply rule on corresponding queue(s)
          2.  If rule verification passes, remove consumed items from the
              corresponding queue(s) and continue with next rule

  <Arguments>
    source_name:
            The name of the item (Step or Inspection) being verified
            (used for user logging).

    source_type:
            "materials" or "products" depending on whether the rules were in the
            "expected_materials" or "expected_products" field.

    rules:
            The list of rules (material or product rules) for the item
            being verified.

    links:
            A dictionary containing link metadata per step or inspection, e.g.:
            {
              <link name> : <Metablock containing a Link object>,
              ...
            }


  <Exceptions>
    FormatError
        if source_type is not "materials" or "products"
    RuleVerficationError
        if the artifacts queue is not empty after all rules were applied

  <Side Effects>
    None.

  """

  source_materials = links[source_name].signed.materials
  source_products = links[source_name].signed.products

  source_materials_queue = list(source_materials.keys())
  source_products_queue = list(source_products.keys())

  # Create generic source artifacts list and queue depending on the source type
  if source_type == "materials":
    source_artifacts = source_materials
    source_artifacts_queue = source_materials_queue

  elif source_type == "products":
    source_artifacts = source_products
    source_artifacts_queue = source_products_queue

  else:
    raise securesystemslib.exceptions.FormatError(
        "Argument 'source_type' of function 'verify_item_rules' has to be"
        " one of 'materials' or 'products.'\n"
        "Got:\n\t'{}'".format(source_type))


  # Apply (verify) all rule
  for rule in rules:

    log.info("Verifying '{}'...".format(" ".join(rule)))

    # Unpack rules for dispatching and rule format verification
    rule_data = in_toto.rulelib.unpack_rule(rule)
    rule_type = rule_data["rule_type"]

    # MATCH, ALLOW, DISALLOW operate equally on either products or materials
    # depending on the source_type
    if rule_type == "match":
      source_artifacts_queue = verify_match_rule(
          rule, source_artifacts_queue, source_artifacts, links)

    elif rule_type == "allow":
      source_artifacts_queue = verify_allow_rule(rule, source_artifacts_queue)

    elif rule_type == "disallow":
      verify_disallow_rule(rule, source_artifacts_queue)


    # CREATE, DELETE and MODIFY always operate either on products, on materials
    # or both, independently of the source_type ...
    elif rule_type == "create":
      source_products_queue = verify_create_rule(
          rule, source_materials_queue, source_products_queue)

      # The create rule only updates the products_queue, which in turn
      # only affects the generic artifacts queue if source_type is "products"
      if source_type == "products":
        source_artifacts_queue = source_products_queue

    elif rule_type == "delete":
      source_materials_queue = verify_delete_rule(
          rule, source_materials_queue, source_products_queue)

      # The delete rule only updates the materials_queue, which in turn
      # only affects the generic artifacts queue if source_type is "materials"
      if source_type == "materials":
        source_artifacts_queue = source_materials_queue

    # NOTE: Can't reach `else` branch, if the rule is none of these types
    # an exception would have been raised above in `unpack_rule`
    elif rule_type == "modify": # pragma: no branch
      source_materials_queue, source_products_queue = verify_modify_rule(
          rule, source_materials_queue, source_products_queue,
          source_materials, source_products)

      # The modify rule updates materials_queue and products_queue. We have to
      # update the generic artifacts queue accordingly.
      if source_type == "materials":
        source_artifacts_queue = source_materials_queue

      # NOTE: Can't reach `else` branch, if the source_type is none of these
      # types an exception would have been raised above in `unpack_rule`
      elif source_type == "products": # pragma: no branch
        source_artifacts_queue = source_products_queue


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


def verify_sublayouts(layout, chain_link_dict):
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

        # Make a recursive call to in_toto_verify with the
        # layout and the extracted key object
        summary_link = in_toto_verify(link, layout_key_dict)

        # Replace the layout object in the passed chain_link_dict
        # with the link file returned by in-toto-verify
        key_link_dict[keyid] = summary_link

  return chain_link_dict

def get_summary_link(layout, reduced_chain_link_dict):
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
  # steps appear in the layout
  first_step_link = reduced_chain_link_dict[layout.steps[0].name]
  last_step_link = reduced_chain_link_dict[layout.steps[-1].name]

  summary_link.materials = first_step_link.signed.materials
  summary_link.name = first_step_link.signed.name

  summary_link.products = last_step_link.signed.products
  summary_link.byproducts = last_step_link.signed.byproducts
  summary_link.command = last_step_link.signed.command

  return Metablock(signed=summary_link)

def in_toto_verify(layout, layout_key_dict):
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
            NOTE: Replaces the layout object in the chain_link_dict with an
            unsigned summary link (the actual links of the sublayouts are
            verified). The summary link is used just like a regular link
            to verify command alignments, thresholds and inspections below.

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

  log.info("Reading link metadata files...")
  chain_link_dict = load_links_for_layout(layout)

  log.info("Verifying link metadata signatures...")
  chain_link_dict = verify_link_signature_thresholds(layout, chain_link_dict)

  log.info("Verifying sublayouts...")
  chain_link_dict = verify_sublayouts(layout, chain_link_dict)

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
  return get_summary_link(layout, reduced_chain_link_dict)
