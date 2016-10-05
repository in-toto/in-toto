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

Verification:
    1. Load root layout
      - Search for one of
        - passed layout name, or
        - 'root.layout' in current directory
        - in a bundle?

      - Check if properly formatted
    2. Load root key
      - by passed name
    3. Check signature of layout
    4. For each step in layout
      - Load link and add to link list
      - Check if poprerly formatted
    5. For each inspection
      - Execute with toto-run and add to link list

    6. For each link in link list
      - Check signature
      - Check matchrule
      - Check command

"""
import sys

import toto.util
import toto.runlib
import toto.models.layout
import toto.models.link
import toto.models.matchrule
import toto.ssl_crypto.keys
import toto.log as log

def toto_verify(layout_path, layout_key):

  # Load layout (validates format)
  try:
    log.doing("load root layout '%s'" % layout_path)
    layout = toto.models.layout.Layout.read_from_file(layout_path)
  except Exception, e:
    log.error("something went wrong while loading layout - %s" % e)
    sys.exit(1) # XXX LP: re-raise?

  try:
    log.doing("load root layout key '%s'" % layout_key)
    # XXX LP: Change key load
    layout_key_dict = toto.util.create_and_persist_or_load_key(layout_key)
  except Exception, e:
    log.error("something went wrong while loading key - %s" % e)

  # Verify signature for
  try:
    log.doing("verify layout signature of '%s' with key '%s'" \
        % (layout_path, layout_key))
    if layout.verify_signature(layout_key_dict):
      log.passing("signature verification of layout '%s'" % layout_path)
    else:
      log.failing("signature verification of layout '%s'" % layout_path)
  except Exception, e:
    log.error("something went wrong while verifying signature - %s" % e)

    raise # XXX LP: exit gracefully instead of exception?

  step_links = {}

  # Load links by steps
  for step in layout.steps:
    try:
      step_name = "%s.link" % step.name
      link = toto.models.link.Link.read_from_file(step_name)
      log.doing("load link '%s' " % step_name)
    except Exception, e:
      log.error("something went wrong while loading link - %s" % e)
    else:
      step_links[step.name] = link

      # Fetching keys from layout
      log.doing("fetch keys for link '%s' from layout '%s'" \
          % (step.name, layout_path))
      keys = []
      for keyid in step.pubkeys:
        key = layout.keys.get(keyid)
        if key:
          keys.append(key)
        else:
          log.failing("could not fetch key '%s'" % keyid)

      for key in keys:
        try:
          log.doing("verify link signature of '%s'" % step.name)
          if link.verify_signature(key):
            log.passing("signature verification of link '%s'" % step.name)
          else:
            log.failing("signature verification of link '%s'" % step.path)
        except Exception, e:
          log.error("something went wrong while verifying signature - %s" % e)

      # Check expected command
      try:
        log.doing("align actual command with expected command of '%s'" \
            % step.name)

        # XXX LP: We have to know for sure if both are lists or not!!
        # Then we can validate and convert (if necessary) this in the model
        expected_cmd = step.expected_command.split()
        ran_cmd = link.ran_command

        expected_cmd_cnt = len(expected_cmd)
        ran_cmd_cnt = len(ran_cmd)

        if expected_cmd_cnt != ran_cmd_cnt:
          log.failing("commands '%s' and '%s' have diffent lengths" \
              % (expected_cmd, ran_cmd))

        for i in range(min(expected_cmd_cnt, ran_cmd_cnt)):
          if expected_cmd[i] != ran_cmd[i]:
              log.failing("commands '%s' and '%s' don't align" \
                  % (expected_cmd, ran_cmd))

        else:
          log.passing("command alignment")
      except Exception, e:
        log.error("something went wrong while aligning commands - %s" % e)

  inspect_links = {}
  # Execute inspections and generate link metadata
  for inspection in layout.inspect:
    try:
      log.doing("run inspection '%s' ..." % inspection.name)

      # XXX LP: What should we record as material/product?
      # Is the current directory a sensible default? In general?
      # If so, we should propably make it a default in run_link
      # We could use matchrule paths

      # XXX LP: Is inspect.run a string or a list?
      # The specs says string, the code needs a list? Maybe split
      # the string in toto_run
      link = toto.runlib.run_link(inspection.name, ".", ".",
          inspection.run.split())

    except Exception, e:
      log.error("something went wrong while running inspection - %s" % e)
    else:
      inspect_links[inspection.name] = link

  def _verify_rule(rule, src_materials, src_products,
      src_artifacts, links):
    """ Demultiplexes rules by class type (they have to be called
      with different arguments) """
    if isinstance(rule, toto.models.matchrule.Create) or \
        isinstance(rule, toto.models.matchrule.Delete) or \
        isinstance(rule, toto.models.matchrule.Modify):
      rule.verify_rule(src_materials, src_products)
    elif isinstance(rule, toto.models.matchrule.MatchProduct) or \
        isinstance(rule, toto.models.matchrule.MatchMaterial):
      rule.verify_rule(src_artifacts, links)

  def _verify_rules(rules, src_materials, src_products,
      src_artifacts, links):
    """ Iterates over list of rules and calls verify on them. """
    for rule_data in rules:
      try:
        rule = toto.models.matchrule.Matchrule.read(rule_data)
        _verify_rule(rule, src_materials, src_products, src_artifacts, links)
      except toto.models.matchrule.RuleVerficationFailed, e:
        log.failing(e)
      else:
        log.passing("verification of rule '%s'" % list(rule))

  def _verify_all(items, item_links, links):
    """ Iterates over a list of items (steps or inspects) call verify rules
    for material_matchrules and product_matchrules. """
    for item in items:
      src_materials = item_links[item.name].materials
      src_products = item_links[item.name].products

      log.doing("verify material matchrules of '%s'" % item.name)
      _verify_rules(item.material_matchrules, src_materials,
          src_products, src_materials, links)

      log.doing("verify product matchrules of '%s'" % item.name)
      _verify_rules(item.product_matchrules, src_materials,
          src_products, src_materials, links)

  try:
    log.doing("verify step matchrules")
    _verify_all(layout.steps, step_links, step_links)
  except Exception, e:
    log.error("something went wrong while verifying step matchrules - %s" % e)

  try:
    log.doing("verify inspect matchrules")
    _verify_all(layout.inspect, inspect_links, step_links)
  except Exception, e:
    log.error("something went wrong while verifying inspect matchrules - %s" % e)
