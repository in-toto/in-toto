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

from collections import OrderedDict
import toto.util
import toto.ssl_crypto.keys
import toto.models
import toto.runlib


def toto_verify(layout_path, layout_key):
  """
  XXX LP: What should we do with exceptions?
  Catch? Print? Re-raise? Let be?

  Think about verbosity in general!
  """

  # Load layout (validates format)
  try:
    print "Loading layout '%s' ...", layout_path
    layout = toto.models.layout.Layout.read_from_file(layout_path)
  except Exception, e:
    print e

  # Verify signature for
  try:
    print "Verfying signature ..."
    if layout.verify_signature(layout_key):
      print "Result: GOOD signature"
    else:
      print "Result: BAD signature"
  except Exception, e:
    print e

  step_links = {}

  # Load links by steps
  for step in layout.steps:
    try:
      print "Loading step data (link) '%s' ..." % step.name
      step_name = "%s.link" % step.name
      link = toto.models.link.Link.read_from_file(step_name)
    except Exception, e:
      print e
    else:
      step_links[step_name] = link

      # Fetching keys from layout
      print "Fetching link keys from layout ..."
      keys = []
      for keyid in step.pubkeys:
        key = layout.keys.get(keyid)
        if key:
          keys.append(key)
        else:
          print "BAD: Could not find key '%s' in layout" % keyid

      for key in keys:
        try:
          print "Verfying link signature with key '%s'..." % key["keyid"]
          if link.verify_signature(key):
            print "Result: GOOD signature"
          else:
            print "Result: BAD signature"
        except Exception, e:
          print e

      # Check expected command
      try:
        print "Verfying expected command ..."
        # XXX LP: We have to know for sure if both are lists or not!!
        # Then we can validate and convert (if necessary) this in the model
        expected_cmd = step.expected_command.split()
        ran_cmd = link.ran_command

        expected_cmd_cnt = len(expected_cmd)
        ran_cmd_cnt = len(ran_cmd_cnt)

        if expected_cmd_cnt != ran_cmd_cnt:
          print "Result: BAD command length"

        for i in range(min(expected_cmd_cnt, ran_cmd_cnt)):
          if expected_cmd[i] != ran_cmd[i]:
            print "Result: BAD command alignment - expected: '%s', ran: '%s" \
                % (str(expected_cmd), str(ran_cmd))
            break
        else:
          print "Result: GOOD command alignment"

  inspect_links = {}

  # Execute inspections and generate link metadata
  for inspection in layout.inspect:
    try:
      print "Running inspection  '%s' ..." % inspection.name

      # XXX LP: What should we record as material/product?
      # Is the current directory a sensible default? In general?
      # If so, we should propably make it a default in run_link
      # We could use matchrule paths

      # XXX LP: Is inspect.run a string or a list?
      # The specs says string, the code needs a list? Maybe split
      # the string in toto_run
      link = toto.runlib.run_link(inspection.name, ".", ".",
        inspect.run.split())
    except Exception, e:
      print e
    else:
      inspect_links[inspection.name] = link

  def _verify_rule(rule, src_materials, src_products,
      src_artifacts, links):
    """ Demultiplexes rules by class type (they have to be called
      with different arguments) """
    if isinstance(rule, toto.models.matchrule.Create) or
        isinstance(rule, toto.models.matchrule.Delete) or
        isinstance(rule, toto.models.matchrule.Modify):
      rule.verify_match(src_materials, src_products)
    elif isinstance(rule, toto.models.matchrule.Matchproduct) or
        isinstance(rule, toto.models.matchrule.Matchmaterial):
      rule.verify_match(src_artifacts, links)

  def _verify_rules(rules, src_materials, src_products,
      src_artifacts, links):
    """ Iterates over list of rules and calls verify on them. """
    for rule_data in rules:
      rule = toto.models.matchrule.Matchrule.read(rule_data)
      _verify_rule(rule, src_materials, src_products, src_artifacts, links)

  def _verify_all(items, item_links, links):
    """ Iterates over a list of items (steps or inspects) call verify rules
    for material_matchrules and product_matchrules. """
    for item in items:
      src_materials = item_links[item.name].materials
      src_products = item_links[item.name].products

      _verify_rules(item.material_matchules, src_materials,
          src_products, src_materials, links)

      _verify_rules(item.product_matchrules, src_materials,
          src_products, src_materials, link)

  print "Verifying step matchrules ..."
  _verify_all(layout.steps, step_links, step_links)
  print "Verifying inspect matchrules ..."
  _verify_all(layout.inspect, inspect_links, step_links)
