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

  Provides a library to verify a in_toto final product containing
  a software supply chain layout.

  The library provides functions to:
    - verify signatures of a layout
    - verify signatures of a link
    - verify if the expected command of a step aligns with the actual command
      as recorded in the link metadata file.
    - run inspections (records link metadata)
    - verify product or material matchrules for steps or inspections

"""

import os
import datetime
import iso8601
import fnmatch
from dateutil import tz

import securesystemslib.exceptions

import in_toto.settings
import in_toto.util
import in_toto.runlib
import in_toto.models.layout
import in_toto.models.link
from in_toto.exceptions import (RuleVerficationError, LayoutExpiredError,
    BadReturnValueError)
import in_toto.artifact_rules
import in_toto.log as log

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


def run_all_inspections(layout):
  """
  <Purpose>
    Extracts all inspections from a passed Layout's inspect field and
    iteratively runs each inspections command as defined in the in Inspection's
    run field using in-toto runlib.  This producces link metadata which is
    returned as a dictionary with the according inspection names as keys and
    the Link metadata objects as values.
    If a link command returns non-zero the verification is aborted.

  <Arguments>
    layout:
            A Layout object which is used to extract the Inpsections.

  <Exceptions>
    Calls function that raises BadReturnValueError if an inspection returned
    non-int or non-zero.

  <Side Effects>
    Executes the Inspection command and produces Link metadata.

  <Returns>
    A dictionary containing one Link metadata object per Inspection where
    the key is the Inspection name.
  """
  inspection_links_dict = {}
  for inspection in layout.inspect:
    # FIXME: We don't want to use the base path for runlib so we patch this
    # for now. This will not stay!
    base_path_backup = in_toto.settings.ARTIFACT_BASE_PATH
    in_toto.settings.ARTIFACT_BASE_PATH = None

    # FIXME: What should we record as material/product?
    # Is the current directory a sensible default? In general?
    # If so, we should probably make it a default in run_link
    # We could use matchrule paths.
    material_list = product_list = ["."]
    link = in_toto.runlib.in_toto_run(inspection.name, material_list,
        product_list, inspection.run.split())

    _raise_on_bad_retval(link.return_value, inspection.run)

    inspection_links_dict[inspection.name] = link

    # Dump the inspection link file for auditing
    # Keep in mind that this pollutes the verifier's (client's) filesystem.
    link.dump()

    in_toto.settings.ARTIFACT_BASE_PATH = base_path_backup

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
    LayoutExpiredError
    TBA (see https://github.com/in-toto/in-toto/issues/6)

  <Side Effects>
    None.

  """
  expire_datetime = iso8601.parse_date(layout.expires)
  if expire_datetime < datetime.datetime.now(tz.tzutc()):
    raise LayoutExpiredError("Layout expired")


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
            securesystemslib.formats.KEYDICT_SCHEMA.

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
            securesystemslib.formats.KEYDICT_SCHEMA.

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


def verify_all_steps_command_alignment(layout, links_dict):
  """
  <Purpose>
    Iteratively checks if all expected commands as defined in the
    Steps of a Layout align with the actual commands as recorded in the Link
    metadata.

  <Arguments>
    layout:
            A Layout object to extract the expected commands from.
    links_dict:
            A dictionary of Link metadata objects with Link names as keys.

  <Exceptions>
    None.

  <Side Effects>
    None.

  """
  for step in layout.steps:
    # Find the according link for this step
    link = links_dict[step.name]
    command = link.command
    expected_command = step.expected_command.split()
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
            A dictionary of Link objects with Link names as keys.
            The Link objects relate to Steps or Inspections. The contained
            materials and products are used as rule destination.

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
  rule_data = in_toto.artifact_rules.unpack_rule(rule)
  dest_name = rule_data["dest_name"]
  dest_type = rule_data["dest_type"]

  # Extract destination link
  try:
    dest_link = links[dest_name]
  except Exception as e:
    raise RuleVerficationError("Rule {rule} failed, destination link"
        " '{dest_link}' not found in link dictionary".format(
        rule=rule, dest_link=dest_name))

  # Extract destination artifacts from destination link
  if dest_type.lower() == "materials":
    dest_artifacts = dest_link.materials
  elif dest_type.lower() == "products":
    dest_artifacts = dest_link.products

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
      raise RuleVerficationError("Rule {rule} failed, destination artifact"
          " '{path}' not found in {type} of '{name}'".format(
          rule=rule, path=full_dest_path, name=dest_name, type=dest_type))

    # Compare the hashes of source and destination artifacts
    if source_artifact != dest_artifact:
      raise RuleVerficationError("Rule {rule} failed, source artifact"
          " '{source}' and destination artifact '{dest}' hashes don't match."
          .format(rule=rule, source=full_source_path, dest=full_dest_path))

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
  rule_data = in_toto.artifact_rules.unpack_rule(rule)


  matched_products = fnmatch.filter(
      source_products_queue, rule_data["pattern"])

  for matched_product in matched_products:
    if matched_product in source_materials_queue:
      raise RuleVerficationError("Rule '{0}' failed, product '{1}' was found"
          " in materials but should have been newly created."
          .format(rule, matched_product))

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
  rule_data = in_toto.artifact_rules.unpack_rule(rule)

  matched_materials = fnmatch.filter(
      source_materials_queue, rule_data["pattern"])

  for matched_material in matched_materials:
    if matched_material in source_products_queue:
      raise RuleVerficationError("Rule '{0}' failed, material '{1}' was found"
          " in products but should have been deleted."
          .format(rule, matched_material))

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
  rule_data = in_toto.artifact_rules.unpack_rule(rule)

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
      .format(rule, ", ".join(matched_materials_only)))

  if len(matched_products_only):
    raise RuleVerficationError("Rule '{0}' failed, the following paths appear"
      " as products but not as materials:\n\t{1}"
      .format(rule, ", ".join(matched_products_only)))

  # If we haven't failed yet the two sets are equal and we can test their
  # hash in-equalities
  for path in matched_materials:
    # Is it okay to assume that path returns an artifact? The path
    # should not be in the queues, if it is not in the artifact dictionaries
    if source_materials[path] == source_products[path]:
      raise RuleVerficationError("Rule '{0}' failed, material and product '{1}'"
      " have the same hash (were not modified)."
      .format(rule, path))

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
  rule_data = in_toto.artifact_rules.unpack_rule(rule)

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
  rule_data = in_toto.artifact_rules.unpack_rule(rule)

  matched_artifacts = fnmatch.filter(
      source_artifacts_queue, rule_data["pattern"])

  if len(matched_artifacts):
    raise RuleVerficationError("Rule {0} failed, pattern matched disallowed"
        " artifacts: '{1}' ".format(rule, matched_artifacts))


def verify_item_rules(source_name, source_type, rules, links):
  """
  <Purpose>
    Iteratively apply passed material or product rules to enforce and authorize
    artifacts reported by a link and/or to guarantee that artifacts are linked
    together across links.

  <Algorithm>
      1.  Create materials queue and products queue, and a generic artifacts
          queue based on the source_type (materials or products)
      2.  For each rule:
          1.  Apply rule on queues
          2.  If rule verification passes, update queues and continue

      3.  After applying all rules the artifact queue must be empty. Raise
          and exception otherwise.

  <Arguments>
    source_name:
            The name of the item (Step or Inspection) being verified
            (used for user logging).

    source_type:
            "materials" or "products" depending on whether the rules were in the
            "material_matchrules" or "product_matchrules" field.

    rules:
            The list of rules (material or product rules) for the item
            being verified.

    links:
            A dictionary of all Link objects with Link names as keys.
            The Link objects relate to Steps or inspections and contain the
            source and destination materials and products.


  <Exceptions>
    FormatError
        if source_type is not "materials" or "products"
    RuleVerficationError
        if the artifacts queue is not empty after all rules were applied

  <Side Effects>
    None.

  """

  source_materials = links[source_name].materials
  source_products = links[source_name].products

  source_materials_queue = source_materials.keys()
  source_products_queue = source_products.keys()

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

    # Unpack rules for dispatching and rule format verification
    rule_data = in_toto.artifact_rules.unpack_rule(rule)
    rule_type = rule_data["type"]

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

    elif rule_type == "modify":
      source_materials_queue, source_products_queue = verify_modify_rule(
          rule, source_materials_queue, source_products_queue,
          source_materials, source_products)

      # The modify rule updates materials_queue and products_queue. We have to
      # update the generic artifacts queue accordingly.
      if source_type == "materials":
        source_artifacts_queue = source_materials_queue
      elif source_type == "products":
        source_artifacts_queue = source_products_queue

  # All artifacts have to be consumed by a rule. If we have applied all rules
  # of a list and there are still artifacts in the queue, we fail.
  if source_artifacts_queue:
    raise RuleVerficationError("{0} '{1}' were not authorized by any rule"
        " of item '{2}'".format(
        source_type, source_artifacts_queue, source_name))


def verify_all_item_rules(items, links):
  """
  <Purpose>
    Iteratively verifies material matchrules and product matchrules of
    passed items (Steps or Inspections).

  <Arguments>
    items:
            A list containing Step or Inspection objects whose material
            and product matchrules will be verified.

    links:
            A dictionary of Link objects with Link names as keys. For each
            passed item (Step or Inspection) to be verified, the related Link
            object is taken from this list.

  <Exceptions>
    None.

  <Side Effects>
    None.

  """

  for item in items:

    link = links[item.name]
    log.doing("Verifying material rules for '{}'...".format(item.name))
    verify_item_rules(item.name, "materials", item.material_matchrules, links)

    log.doing("Verifying product rules for '{}'...".format(item.name))
    verify_item_rules(item.name, "products", item.product_matchrules, links)


def in_toto_verify(layout_path, layout_key_paths):
  """
  <Purpose>
    Does entire in-toto supply chain verification of a final product
    by performing the following actions:
        1.  Load root layout as specified by 'layout_path'
        2.  Load root layout signing key(s) (project owner public key(s)) as
            specified by 'layout_key_paths'
        3.  Verify layout signature(s)
        4.  Verify layout expiration
        5.  Load link metadata for every Step defined in the layout
            NOTE: in_toto_verify searches for link metadata files by their step
            name plus the extension '.link' in the current directory.
            E.g. a step of name 'foo' is expected to be found in the current
            directory at 'foo.link'.
        6.  Verify functionary signature for every Link.
        7.  Verify alignment of defined (Step) and reported (Link) commands
            NOTE: Won't raise exception on mismatch
        8.  Execute Inspection commands
            NOTE: Inspections, similar to Steps executed with 'in-toto-run',
            will record materials before and products after command execution.
            For now it records everything in the current working directory.
        9.  Verify rules defined in each Step's material_matchrules and
            product_matchrules field.
       10.  Verify rules defined in each Inspection's material_matchrules and
            product_matchrules field.

    Note, this function will read the following files from disk:
      - software supply chain layout
      - project owner public key(s)
      - link metadata files

  <Arguments>
    layout_path:
            Path to the layout that is being verified.

    layout_key_paths:
            List of paths to project owner public keys, used to verify the
            layout's signature.

  <Exceptions>
    None.

  <Side Effects>
    None.

  """

  log.doing("Verifying software supply chain...")

  log.doing("Reading layout...")
  layout = in_toto.models.layout.Layout.read_from_file(layout_path)

  log.doing("Reading layout key(s)...")
  layout_key_dict = in_toto.util.import_rsa_public_keys_from_files_as_dict(
      layout_key_paths)

  log.doing("Verifying layout signatures...")
  verify_layout_signatures(layout, layout_key_dict)

  log.doing("Verifying layout expiration... ")
  verify_layout_expiration(layout)

  log.doing("Reading link metadata files...")
  step_link_dict = layout.import_step_metadata_from_files_as_dict()

  log.doing("Verifying link metadata signatures...")
  verify_all_steps_signatures(layout, step_link_dict)

  log.doing("Verifying alignment of reported commands...")
  verify_all_steps_command_alignment(layout, step_link_dict)

  log.doing("Executing Inspection commands...")
  inspection_link_dict = run_all_inspections(layout)

  # Combine step links and inspection links for rule verification
  # (Python 2 only)
  link_dict = dict(step_link_dict.items() + inspection_link_dict.items())

  log.doing("Verifying Step rules...")
  verify_all_item_rules(layout.steps, link_dict)

  log.doing("Verifying Inspection rules...")
  verify_all_item_rules(layout.inspect, link_dict)

  # We made it this far without exception that means, verification passed.
  log.passing("Passing verification")
