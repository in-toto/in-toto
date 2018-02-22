#!/usr/bin/env python
"""
<Program Name>
  layout.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>
  Santiago Torres <santiago@nyu.edu>

<Started>
  Sep 23, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides classes related to the definition of a software supply chain.

<Classes>
  Layout:
      represents the metadata file that defines a software supply chain through
      steps and inspections

  Step:
      represents one step of the software supply chain, performed by one or many
      functionaries, who are identified by a key also stored to the layout

  Inspection:
      represents a hook that is run at verification
"""
from six import string_types

import attr
import shlex
import json

from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

from in_toto.models.common import Signable, ValidationMixin
import in_toto.rulelib
import in_toto.exceptions
import in_toto.formats

import securesystemslib.exceptions
import securesystemslib.formats
import securesystemslib.schema
import securesystemslib.interface


# Link metadata for sublayouts are expected to be found in a subdirectory
# with the following name, relative to the verification directory
SUBLAYOUT_LINK_DIR_FORMAT = "{name}.{keyid:.8}"



@attr.s(repr=False, init=False)
class Layout(Signable):
  """
  A layout lists the sequence of steps of the software supply chain, and the
  functionaries authorized to perform these steps.

  The object should be wrapped in a metablock object, to provide functionality
  for signing and signature verification, and reading from and writing to disk.

  """
  _type = attr.ib()
  steps = attr.ib()
  inspect = attr.ib()
  keys = attr.ib()
  expires = attr.ib()
  readme = attr.ib()


  def __init__(self, **kwargs):
    """
    <Purpose>
      Instantiate a new layout object with optional initial values.

    <Optional Keyword Arguments>
      steps:
              A list of step objects describing the steps required to carry out
              the software supply chain.

      inspect:
              A list of inspection objects describing any additional actions
              carried out upon verification.

      keys:
              A dictionary of public keys whose private keys are used
              to sign the metadata (link metadata) corresponding to the steps
              of the supply chain. Each step can authorize one or more of the
              here listed keys individually.

      expires:
              The expiration date of a layout.

      readme:
              A human readable description of the software supply chain defined
              by the layout.

    <Exceptions>
      securesystemslib.exceptions.FormatError
              If the instantiated layout has invalid properties, e.g. because
              any of the assigned keyword arguments are invalid.

    """
    super(Layout, self).__init__()
    self._type = "layout"
    self.steps = kwargs.get("steps", [])
    self.inspect = kwargs.get("inspect", [])
    self.keys = kwargs.get("keys", {})
    self.readme = kwargs.get("readme", "")

    # Assign a default expiration (one month) if not expiration date is passed
    # TODO: Is one month a sensible default? In any case, we need a valid
    # expiration date in order for the layout object to validate.
    # (see self._validate_expires)
    self.expires = kwargs.get("expires")
    if not self.expires:
      self.set_relative_expiration(months=1)

    # TODO: Should we validate in the constructor or allow the user to create
    # an invalid layout and call validate explicitly?
    self.validate()


  @property
  def type_(self):
    """
    <Purpose>
      Getter for protected _type attribute.

      NOTE: The trailing underscore used is by convention (pep8) to avoid
      conflicts with Python's 'type' keyword.

    <Returns>
      The type of the metadata object, i.e. "layout" (see constructor).

    """
    return self._type


  @staticmethod
  def read(data):
    """
    <Purpose>
      Static method to instantiate a layout object from a Python dictionary,
      e.g. by parsing its JSON representation. The method expects any
      contained steps and inspections to be Python dictionaries as well, and
      tries to instantiate the corresponding objects using the step's and
      inspection's read methods respectively.

    <Arguments>
      data:
              A dictionary containing layout metadata.

    <Exceptions>
      securesystemslib.exceptions.FormatError
              If any of the layout's properties is invalid.

    <Returns>
      The newly created layout object, optionally containing newly instantiated
      step and inspection objects.

    """
    steps = []

    for step_data in data.get("steps"):
      steps.append(Step.read(step_data))
    data["steps"] = steps

    inspections = []
    for inspect_data in data.get("inspect"):
      inspections.append(Inspection.read(inspect_data))
    data["inspect"] = inspections

    return Layout(**data)


  def set_relative_expiration(self, days=0, months=0, years=0):
    """
    <Purpose>
      Set the layout's expiration date in one or more of "days", "months" or
      "years" from today. If no argument is passed, it defaults to today.

    <Arguments>
      days:
              Days from today.

      months:
              Months from today.

      years:
              Years from today.

    <Exceptions>
      securesystemslib.exceptions.FormatError
              If any of days, months or years is passed and is not an
              integer.

    """
    securesystemslib.schema.Integer().check_match(days)
    securesystemslib.schema.Integer().check_match(months)
    securesystemslib.schema.Integer().check_match(years)

    self.expires = (datetime.today() + relativedelta(
        days=days, months=months, years=years)).strftime("%Y-%m-%dT%H:%M:%SZ")


  def get_step_name_list(self):
    """
    <Purpose>
      Return list of step names in the order in which they are listed in the
      layout.

    <Returns>
      A list of step names.

    """
    step_names = []
    for step in self.steps:
      step_names.append(step.name)

    return step_names


  def get_step_by_name(self, step_name):
    """
    <Purpose>
      Return the first step in the layout's list of steps identified by the
      passed step name.

      NOTE: Step names must be unique within a layout, which is enforced by
      they Layout's validate method. However, if validate has not been called,
      there may be multiple steps with the same name. In that case only
      the first step with the passed name is returned.

    <Arguments>
      step_name:
              A step name.

    <Exceptions>
      securesystemslib.exceptions.FormatError
              If the passed step name is not a string.

    <Returns>
      A step object.

    """
    securesystemslib.schema.AnyString().check_match(step_name)

    for step in self.steps: # pragma: no branch
      if step.name == step_name:
        return step


  def remove_step_by_name(self, step_name):
    """
    <Purpose>
      Remove all steps from the layout's list of steps identified by the
      passed step name.

      NOTE: Step names must be unique within a layout, which is enforced by
      they layout's validate method. However, if validate has not been called,
      there might be multiple steps with the same name. The method removes
      all steps with the passed name.

    <Arguments>
      step_name:
              A step name.

    <Exceptions>
      securesystemslib.exceptions.FormatError
              If the passed step name is not a string.

    """
    securesystemslib.schema.AnyString().check_match(step_name)

    for step in self.steps:
      if step.name == step_name:
        self.steps.remove(step)


  def get_inspection_name_list(self):
    """
    <Purpose>
      Return list of inspection names in the order in which they are listed in
      the layout.

    <Returns>
      A list of the inspection names.

    """
    inspection_names = []
    for inspection in self.inspect:
      inspection_names.append(inspection.name)

    return inspection_names


  def get_inspection_by_name(self, inspection_name):
    """
    <Purpose>
      Return the first inspection in the layout's list of inspections
      identified by the passed inspection name.

      NOTE: Inspection names must be unique within a layout, which is enforced
      by they layout's validate method. However, if validate has not been
      called, there may be multiple inspections with the same name. In that
      case only the first inspection with the passed name is returned.

    <Arguments>
      inspection_name:
              An inspection name.

    <Exceptions>
      securesystemslib.exceptions.FormatError
              If the passed inspection name is not a string.

    <Returns>
      An inspection object.

    """
    securesystemslib.schema.AnyString().check_match(inspection_name)

    for inspection in self.inspect: # pragma: no branch
      if inspection.name == inspection_name:
        return inspection


  def remove_inspection_by_name(self, inspection_name):
    """
    <Purpose>
      Remove all inspections from the layout's list of inspections identified
      by the passed inspection name.

      NOTE: Inspection names must be unique within a layout, which is enforced
      by they layout's validate method. However, if validate has not been
      called, there may be multiple inspections with the same name. The
      method removes all inspections with the passed name.

    <Arguments>
      inspection_name:
              An inspection name.

    <Exceptions>
      securesystemslib.exceptions.FormatError
              If the passed inspection name is not a string.

    """
    securesystemslib.schema.AnyString().check_match(inspection_name)

    for inspection in self.inspect:
      if inspection.name == inspection_name:
        self.inspect.remove(inspection)


  def get_functionary_key_id_list(self):
    """
    <Purpose>
      Return a list of the functionary keyids from the layout's keys
      dictionary.

    <Returns>
      A list of functionary keyids.

    """
    return list(self.keys.keys())


  def add_functionary_key(self, key):
    """
    <Purpose>
      Add the passed functionary public key to the layout's dictionary of keys.

    <Arguments>
      key:
              A functionary public key conformant with
              in_toto.formats.ANY_PUBKEY_SCHEMA.

    <Exceptions>
      securesystemslib.exceptions.FormatError
              If the passed key does not match
              in_toto.formats.ANY_PUBKEY_SCHEMA.

    <Returns>
      The added functionary public key.

    """
    in_toto.formats.ANY_PUBKEY_SCHEMA.check_match(key)
    keyid = key["keyid"]
    self.keys[keyid] = key
    return key


  def add_functionary_key_from_path(self, key_path):
    """
    <Purpose>
      Load a functionary public key in RSA PEM format from the passed path
      and add it to the layout's dictionary of keys.

    <Arguments>
      key_path:
              A path, conformant with securesystemslib.formats.PATH_SCHEMA,
              to a functionary public key.

    <Exceptions>
      securesystemslib.exceptions.FormatError
              If the passed key path does not match
              securesystemslib.formats.PATH_SCHEMA.

      securesystemslib.exceptions.Error
              If the key at the passed path cannot be imported as public key.

    <Returns>
      The added functionary public key.

    """
    securesystemslib.formats.PATH_SCHEMA.check_match(key_path)
    key = securesystemslib.interface.import_rsa_publickey_from_file(key_path)

    return self.add_functionary_key(key)



  def add_functionary_key_from_gpg_keyid(self, gpg_keyid, gpg_home=None):
    """
    <Purpose>
      Load a functionary public key from the GPG keychain, located at the
      passed GPG home path, identified by the passed GPG keyid, and add it to
      the layout's dictionary of keys.

    <Arguments>
      gpg_keyid:
              A GPG keyid.

      gpg_home:
              A path to the GPG keychain to load the key from. If not passed
              the default GPG keychain is used.

    <Exceptions>
      securesystemslib.exceptions.FormatError
              If the passed gpg keyid does not match
              securesystemslib.formats.KEYID_SCHEMA.

              If the gpg home path is passed and does not match
              securesystemslib.formats.PATH_SCHEMA.

              If the key loaded from the GPG keychain does not match
              in_toto.formats.ANY_PUBKEY_SCHEMA.

    <Returns>
      The added functionary public key.

    """
    securesystemslib.formats.KEYID_SCHEMA.check_match(gpg_keyid)
    if gpg_home: # pragma: no branch
      securesystemslib.formats.PATH_SCHEMA.check_match(gpg_home)

    key = in_toto.gpg.functions.gpg_export_pubkey(gpg_keyid,
        homedir=gpg_home)
    return self.add_functionary_key(key)


  def add_functionary_keys_from_paths(self, key_path_list):
    """
    <Purpose>
      Load the functionary public keys in RSA PEM format from the passed list
      of paths and add them to the layout's dictionary of keys.

    <Arguments>
      key_path_list:
              A list of paths, conformant with
              securesystemslib.formats.PATH_SCHEMA, to functionary public keys.

    <Exceptions>
      securesystemslib.exceptions.FormatError
              If any of the passed key paths does not match
              securesystemslib.formats.PATH_SCHEMA.

      securesystemslib.exceptions.Error
              If any of the keys at the passed paths cannot be imported as
              public key.

    <Returns>
      A dictionary of the added functionary public keys with the key's keyids
      as dictionary keys and the keys as values.

    """
    securesystemslib.formats.PATHS_SCHEMA.check_match(key_path_list)
    key_dict = {}
    for key_path in key_path_list:
      key = self.add_functionary_key_from_path(key_path)
      key_dict[key["keyid"]] = key

    return key_dict


  def add_functionary_keys_from_gpg_keyids(self, gpg_keyid_list,
      gpg_home=None):
    """
    <Purpose>
      Load functionary public keys from the GPG keychain, located at the
      passed GPG home path, identified by the passed GPG keyids, and add it to
      the layout's dictionary of keys.

    <Arguments>
      gpg_keyid_list:
              A list of GPG keyids.

      gpg_home:
              A path to the GPG keychain to load the keys from. If not passed
              the default GPG keychain is used.

    <Exceptions>
      securesystemslib.exceptions.FormatError
              If any of the passed gpg keyids does not match
              securesystemslib.formats.KEYID_SCHEMA.

              If gpg home is passed and does not match
              securesystemslib.formats.PATH_SCHEMA.

              If any of the keys loaded from the GPG keychain does not
              match in_toto.formats.ANY_PUBKEY_SCHEMA.

    <Returns>
      A dictionary of the added functionary public keys with the key's keyids
      as dictionary keys and the keys as values.

    """
    securesystemslib.formats.KEYIDS_SCHEMA.check_match(gpg_keyid_list)
    key_dict = {}
    for gpg_keyid in gpg_keyid_list:
      key = self.add_functionary_key_from_gpg_keyid(gpg_keyid, gpg_home)
      key_dict[key["keyid"]] = key

    return key_dict


  def _validate_type(self):
    """Private method to check that the type string is set to layout."""
    if self._type != "layout":
      raise securesystemslib.exceptions.FormatError(
          "Invalid _type value for layout (Should be 'layout')")


  def _validate_expires(self):
    """Private method to verify if the expiration field has the right format
    and can be parsed."""
    try:
      # We do both 'parse' and 'check_match' because the format check does not
      # detect bogus dates (e.g. Jan 35th) and parse can do more formats.
      parse(self.expires)
      securesystemslib.formats.ISO8601_DATETIME_SCHEMA.check_match(
          self.expires)
    except Exception as e:
      raise securesystemslib.exceptions.FormatError(
          "Malformed date string in layout. Exception: {}".format(e))


  def _validate_readme(self):
    """Private method to check that the readme field is a string."""
    if not isinstance(self.readme, string_types):
      raise securesystemslib.exceptions.FormatError(
          "Invalid readme '{}', value must be a string."
          .format(self.readme))


  def _validate_keys(self):
    """Private method to ensure that the keys contained are right."""
    in_toto.formats.ANY_PUBKEY_DICT_SCHEMA.check_match(self.keys)


  def _validate_steps_and_inspections(self):
    """Private method to verify that the list of steps and inspections are
    correctly formed."""
    names_seen = set()
    if type(self.steps) != list:
      raise securesystemslib.exceptions.FormatError(
          "The steps field should be a list!")

    for step in self.steps:
      if not isinstance(step, Step):
        raise securesystemslib.exceptions.FormatError(
            "The steps list should only contain steps!")

      step.validate()

      if step.name in names_seen:
        raise securesystemslib.exceptions.FormatError(
            "There is already a step with name '{}'. Step names must be"
            " unique within a layout.".format(step.name))
      names_seen.add(step.name)

    if type(self.inspect) != list:
      raise securesystemslib.exceptions.FormatError(
          "The inspect field should a be a list!")

    for inspection in self.inspect:
      if not isinstance(inspection, Inspection):
        raise securesystemslib.exceptions.FormatError(
            "The inspect list should only contain inspections!")

      inspection.validate()

      if inspection.name in names_seen:
        raise securesystemslib.exceptions.FormatError(
            "There is already an inspection with name '{}'. Inspection names"
            " must be unique within a layout.".format(inspection.name))
      names_seen.add(inspection.name)



@attr.s(repr=False, init=False)
class SupplyChainItem(ValidationMixin):
  """
  Parent class for items of the supply chain, i.e. Steps and Inspections.

  """
  name = attr.ib()
  expected_materials = attr.ib()
  expected_products = attr.ib()


  def __init__(self, **kwargs):
    """
    <Purpose>
      Instantiate a new SupplyChainItem object with optional initial values.

    <Optional Keyword Arguments>
      name:
              A unique name used to identify the related link metadata

      expected_materials and expected_products:
              A list of artifact rules used to verify if the materials or
              products of the item (found in the according link metadata file)
              link correctly with other items of the supply chain.

    """
    super(SupplyChainItem, self).__init__()
    self.name = kwargs.get("name")
    self.expected_materials = kwargs.get("expected_materials", [])
    self.expected_products = kwargs.get("expected_products", [])


  def __repr__(self):
    """Returns an indented JSON string of the metadata object. """
    return json.dumps(attr.asdict(self),
        indent=1, separators=(",", ": "), sort_keys=True)


  def add_material_rule_from_string(self, rule_string):
    """
    <Purpose>
      Convenience method to parse the passed rule string into a list and append
      it to the item's list of expected_materials.

    <Arguments>
      rule_string:
              An artifact rule string, whose list representation is parseable
              by in_toto.rulelib.unpack_rule


    <Exceptions>
      securesystemslib.exceptions.FormatError:
              If the passed rule_string is not a string.
              If the parsed rule_string cannot be unpacked using rulelib.

    """
    securesystemslib.schema.AnyString().check_match(rule_string)
    rule_list = shlex.split(rule_string)

    # Raises format error if the parsed rule_string is not a valid rule
    in_toto.rulelib.unpack_rule(rule_list)

    self.expected_materials.append(rule_list)


  def add_product_rule_from_string(self, rule_string):
    """
    <Purpose>
      Convenience method to parse the passed rule string into a list and append
      it to the item's list of expected_products.

    <Arguments>
      rule_string:
              An artifact rule string, whose list representation is parseable
              by in_toto.rulelib.unpack_rule


    <Exceptions>
      securesystemslib.exceptions.FormatError:
              If the passed rule_string is not a string.
              If the parsed rule_string cannot be unpacked using rulelib.

    """
    securesystemslib.schema.AnyString().check_match(rule_string)
    rule_list = shlex.split(rule_string)

    # Raises format error if the parsed rule_string is not a valid rule
    in_toto.rulelib.unpack_rule(rule_list)

    self.expected_products.append(rule_list)


  def _validate_expected_materials(self):
    """Private method to check that material rules are correctly formed."""
    if type(self.expected_materials) != list:
      raise securesystemslib.exceptions.FormatError(
          "Material rules should be a list!")

    for rule in self.expected_materials:
      in_toto.rulelib.unpack_rule(rule)


  def _validate_expected_products(self):
    """Private method to check that product rules are correctly formed."""
    if type(self.expected_products) != list:
      raise securesystemslib.exceptions.FormatError(
          "Product rules should be a list!")

    for rule in self.expected_products:
      in_toto.rulelib.unpack_rule(rule)



@attr.s(repr=False, init=False)
class Step(SupplyChainItem):
  """
  Represents a step of the supply chain performed by a functionary. A step
  relates to link metadata generated when the step was performed.
  Materials and products used/produced by the step are constrained by the
  artifact rules in the step's expected_materials and expected_products
  attributes.

  """
  _type = attr.ib()
  pubkeys = attr.ib()
  expected_command = attr.ib()
  threshold = attr.ib()


  def __init__(self, **kwargs):
    """
    <Purpose>
      Instantiates a new step object with optional initial values.

    <Optional Keyword Arguments>
      name:
              see parent class SupplyChainItem

      expected_materials and expected_products:
              see parent class SupplyChainItem

      pubkeys:
              A list of keyids of the functionaries authorized to perform the
              step

      expected_command:
              The command expected to have performed this step

      threshold:
              The least number of functionaries expected to perform this step

    <Exceptions>
      securesystemslib.exceptions.FormatError
              If the instantiated step has invalid properties, e.g. because
              any of the assigned keyword arguments are invalid.

    """
    super(Step, self).__init__(**kwargs)
    self._type = "step"
    self.pubkeys = kwargs.get("pubkeys", [])
    self.expected_command = kwargs.get("expected_command", [])
    self.threshold = kwargs.get("threshold", 1)

    self.validate()


  @staticmethod
  def read(data):
    """
    <Purpose>
      Static method to instantiate a step object from a Python dictionary,
      e.g. by parsing its JSON representation.

    <Arguments>
      data:
              A dictionary containing step metadata.

    <Exceptions>
      securesystemslib.exceptions.FormatError
              If any of the step's properties is invalid.

    <Returns>
      The newly created step object.

    """
    return Step(**data)


  def set_expected_command_from_string(self, command_string):
    """
    <Purpose>
      Convenience method to parse the passed command_string into a list and
      assign it to the step's expected_command attribute.

    <Arguments>
      command_string:
              A string containing a command and command arguments.

    <Exceptions>
      securesystemslib.exceptions.FormatError
              If the passed command_string is not a string.

    """
    securesystemslib.schema.AnyString().check_match(command_string)
    self.expected_command = shlex.split(command_string)


  def _validate_type(self):
    """Private method to ensure that the type field is set to step."""
    if self._type != "step":
      raise securesystemslib.exceptions.FormatError(
          "Invalid _type value for step (Should be 'step')")


  def _validate_threshold(self):
    """Private method to check that the threshold field is set to an int."""
    if type(self.threshold) != int:
      raise securesystemslib.exceptions.FormatError(
          "Invalid threshold '{}', value must be an int."
          .format(self.threshold))


  def _validate_pubkeys(self):
    """Private method to check that the pubkeys is a list of keyids."""
    if type(self.pubkeys) != list:
      raise securesystemslib.exceptions.FormatError(
          "The pubkeys field should be a list!")

    for keyid in self.pubkeys:
      securesystemslib.formats.KEYID_SCHEMA.check_match(keyid)


  def _validate_expected_command(self):
    """Private method to check that the expected_command is proper."""
    if type(self.expected_command) != list:
      raise securesystemslib.exceptions.FormatError(
          "The expected command field is malformed!")



@attr.s(repr=False, init=False)
class Inspection(SupplyChainItem):
  """
  Represents an inspection whose command in the run attribute is executed
  during final product verification. Materials and products used/produced by
  the inspection are constrained by the artifact rules in the inspection's
  expected_materials and expected_products attributes.

  """
  _type = attr.ib()
  run = attr.ib()


  def __init__(self, **kwargs):
    """
    <Purpose>
        Instantiates a new inspection object with optional initial values.

    <Optional Keyword Arguments>
      name:
              see parent class SupplyChainItem

      expected_materials and expected_products:
              see parent class SupplyChainItem

      run:
              The command to be executed during final product verification

    <Exceptions>
      securesystemslib.exceptions.FormatError
              If the instantiated inspection has invalid properties, e.g.
              because any of the assigned keyword arguments are invalid.

    """
    super(Inspection, self).__init__(**kwargs)
    self._type = "inspection"
    self.run = kwargs.get("run", [])

    self.validate()


  @staticmethod
  def read(data):
    """
    <Purpose>
      Static method to instantiate an inspection object from a Python
      dictionary, e.g. by parsing its JSON representation.

    <Arguments>
      data:
              A dictionary containing inspection metadata.

    <Exceptions>
      securesystemslib.exceptions.FormatError
              If any of the inspection's properties is invalid.

    <Returns>
      The newly created inspection object.

    """
    return Inspection(**data)


  def set_run_from_string(self, command_string):
    """
    <Purpose>
      Convenience method to parse the passed command_string into a list and
      assign it to the inspection's run attribute.

    <Arguments>
      command_string:
              A string containing a command and command arguments.

    <Exceptions>
      securesystemslib.exceptions.FormatError
              If the passed command_string is not a string.

    """
    securesystemslib.schema.AnyString().check_match(command_string)
    self.run = shlex.split(command_string)


  def _validate_type(self):
    """Private method to ensure that the type field is set to inspection."""
    if self._type != "inspection":
      raise securesystemslib.exceptions.FormatError(
          "The _type field must be set to 'inspection'!")


  def _validate_run(self):
    """Private method to check that the expected command is correct."""
    if type(self.run) != list:
      raise securesystemslib.exceptions.FormatError(
          "The run field is malformed!")
