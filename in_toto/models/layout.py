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
      represents one step of the software supply chain, performed by one or
      many functionaries, who are identified by a key also stored to the layout

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

import securesystemslib.exceptions
import securesystemslib.formats
import securesystemslib.schema
import securesystemslib.interface
import securesystemslib.gpg.functions


# Link metadata for sublayouts are expected to be found in a subdirectory
# with the following name, relative to the verification directory
SUBLAYOUT_LINK_DIR_FORMAT = "{name}.{keyid:.8}"



@attr.s(repr=False, init=False)
class Layout(Signable):
  """A definition for a software supply chain.

  A layout lists the sequence of steps of the software supply chain in the
  order they are expected to be performed, the functionaries authorized and
  required to perform them, and inspections to be performed by the client upon
  final product verification.

  A Layout object is usually contained in a generic Metablock object for
  signing, serialization and I/O capabilities.

  Attributes:
    steps: A list of Step objects.

    inspect: A list of Inspection objects.

    keys: A dictionary of functionary public keys, with keyids as dict keys and
        keys as values.

    expires: The layout expiration.

    readme: A human readable description of the software supply chain.

  """
  _type = attr.ib()
  steps = attr.ib()
  inspect = attr.ib()
  keys = attr.ib()
  expires = attr.ib()
  readme = attr.ib()


  def __init__(self, **kwargs):
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
    """The string "layout" to indentify the in-toto metadata type."""
    # NOTE: We expose the type_ property in the API documentation instead of
    # _type to protect it against modification.
    # NOTE: Trailing underscore is used by convention (pep8) to avoid conflict
    # with Python's type keyword.
    return self._type


  @staticmethod
  def read(data):
    """Creates a Layout object from its dictionary representation.

    Arguments:
      data: A dictionary with layout metadata fields.

    Raises:
      securesystemslib.exceptions.FormatError: Passed data is invalid.

    Returns:
      The created Layout object.

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
    """Sets layout expiration relative to today.

    If not argument is passed the set exipration date is now.

    Arguments:
      days (optional): Days from today.
      months (optional): Months from today.
      years (optional): Years from today.

    Raises:
      securesystemslib.exceptions.FormatError: Arguments are not ints.

    """
    securesystemslib.schema.Integer().check_match(days)
    securesystemslib.schema.Integer().check_match(months)
    securesystemslib.schema.Integer().check_match(years)

    self.expires = (datetime.today() + relativedelta(
        days=days, months=months, years=years)).strftime("%Y-%m-%dT%H:%M:%SZ")


  def get_step_name_list(self):
    """Returns ordered list of step names as they appear in the layout.

    Returns:
      A list of step names.

    """
    step_names = []
    for step in self.steps:
      step_names.append(step.name)

    return step_names


  def get_step_by_name(self, step_name):
    """Returns step identified by step_name from the layout.

    NOTE: Returns the first step identified only, which should be the only step
    for a given name of a valid layout.

    Arguments:
      step_name: A step name.

    Raises:
      securesystemslib.exceptions.FormatError: Argument is not a string.

    Returns:
      A Step object.

    """
    securesystemslib.schema.AnyString().check_match(step_name)

    for step in self.steps: # pragma: no branch
      if step.name == step_name:
        return step


  def remove_step_by_name(self, step_name):
    """Removes steps identified by step_name from the layout.

    NOTE: Removes all steps identified, which should be only one step for a
    given name of a valid layout.

    Arguments:
      step_name: A step name.

    Raises:
      securesystemslib.exceptions.FormatError: Argument is not a string.

    """
    securesystemslib.schema.AnyString().check_match(step_name)

    for step in self.steps:
      if step.name == step_name:
        self.steps.remove(step)


  def get_inspection_name_list(self):
    """Returns ordered list of inspection names as they appear in the layout.

    Returns:
      A list of inspection names.

    """
    inspection_names = []
    for inspection in self.inspect:
      inspection_names.append(inspection.name)

    return inspection_names


  def get_inspection_by_name(self, inspection_name):
    """Returns inspection identified by inspection_names from the layout.

    NOTE: Returns the first inspection identified only, which should be the
    only inspection for a given name of a valid layout.

    Arguments:
      inspection_name: An inspection name.

    Raises:
      securesystemslib.exceptions.FormatError: Argument is not a string.

    Returns:
      An Inspection object.

    """
    securesystemslib.schema.AnyString().check_match(inspection_name)

    for inspection in self.inspect: # pragma: no branch
      if inspection.name == inspection_name:
        return inspection


  def remove_inspection_by_name(self, inspection_name):
    """Removes inspections identified by inspection_name from the layout.

    NOTE: Removes all inspections identified, which should be only one
    inspection for a given name of a valid layout.

    Arguments:
      inspection_name: An inspection name.

    Raises:
      securesystemslib.exceptions.FormatError: Argument is not a string.

    """
    securesystemslib.schema.AnyString().check_match(inspection_name)

    for inspection in self.inspect:
      if inspection.name == inspection_name:
        self.inspect.remove(inspection)


  def get_functionary_key_id_list(self):
    """Returns list of functionary keyids from the layout.

    Returns:
      A list of keyids.

    """
    return list(self.keys.keys())


  def add_functionary_key(self, key):
    """Adds key as functionary key to layout.

    Arguments:
      key: A public key. Format is securesystemslib.formats.ANY_PUBKEY_SCHEMA.

    Raises:
      securesystemslib.exceptions.FormatError: Argument is malformed.

    Returns:
      The added key.

    """
    securesystemslib.formats.ANY_PUBKEY_SCHEMA.check_match(key)
    keyid = key["keyid"]
    self.keys[keyid] = key
    return key


  def add_functionary_key_from_path(self, key_path):
    """Loads key from disk and adds as functionary key to layout.

    Arguments:
      key_path: A path to a PEM-formatted RSA public key. Format is
          securesystemslib.formats.PATH_SCHEMA.

    Raises:
      securesystemslib.exceptions.FormatError: Argument is malformed.
      securesystemslib.exceptions.Error: Key cannot be imported.

    Returns:
      The added functionary public key.

    """
    securesystemslib.formats.PATH_SCHEMA.check_match(key_path)
    key = securesystemslib.interface.import_rsa_publickey_from_file(key_path)

    return self.add_functionary_key(key)



  def add_functionary_key_from_gpg_keyid(self, gpg_keyid, gpg_home=None):
    """Loads key from gpg keychain and adds as functionary key to layout.

    Arguments:
      gpg_keyid: A keyid used to identify a local gpg public key.
      gpg_home (optional): A path to the gpg home directory. If not set the
          default gpg home directory is used.

    Raises:
      securesystemslib.exceptions.FormatError: Arguments are malformed.
      securesystemslib.gpg.execeptions.KeyNotFoundError: Key cannot be found.

    Side Effects:
      Calls system gpg command in a subprocess.

    Returns:
      The added key.

    """
    securesystemslib.formats.KEYID_SCHEMA.check_match(gpg_keyid)
    if gpg_home: # pragma: no branch
      securesystemslib.formats.PATH_SCHEMA.check_match(gpg_home)

    key = securesystemslib.gpg.functions.export_pubkey(gpg_keyid,
        homedir=gpg_home)
    return self.add_functionary_key(key)


  def add_functionary_keys_from_paths(self, key_path_list):
    """Loads keys from disk and adds as functionary keys to layout.

    Arguments:
      key_path_list: A list of paths to PEM-formatted RSA public keys. Format
          of each path is securesystemslib.formats.PATH_SCHEMA.

    Raises:
      securesystemslib.exceptions.FormatError: Argument is malformed.
      securesystemslib.exceptions.Error: A key cannot be imported.

    Returns:
      A dictionary of the added functionary keys, with keyids as dictionary
      keys and keys as values.

    """
    securesystemslib.formats.PATHS_SCHEMA.check_match(key_path_list)
    key_dict = {}
    for key_path in key_path_list:
      key = self.add_functionary_key_from_path(key_path)
      key_dict[key["keyid"]] = key

    return key_dict


  def add_functionary_keys_from_gpg_keyids(self, gpg_keyid_list,
      gpg_home=None):
    """Loads keys from gpg keychain and adds as functionary keys to layout.

    Arguments:
      gpg_keyid_list: A list of keyids used to identify local gpg public keys.
      gpg_home (optional): A path to the gpg home directory. If not set the
          default gpg home directory is used.

    Raises:
      securesystemslib.exceptions.FormatError: Arguments are malformed.
      securesystemslib.gpg.execeptions.KeyNotFoundError: A key cannot be found.

    Side Effects:
      Calls system gpg command in a subprocess.

    Returns:
      A dictionary of the added functionary keys, with keyids as dictionary
      keys and keys as values.

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
    securesystemslib.formats.ANY_PUBKEY_DICT_SCHEMA.check_match(self.keys)


  def _validate_steps_and_inspections(self):
    """Private method to verify that the list of steps and inspections are
    correctly formed."""
    names_seen = set()
    if not isinstance(self.steps, list):
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

    if not isinstance(self.inspect, list):
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
  """Common attributes and methods for supply chain steps and inspections.

  Attributes:
    name: A unique named used to associate related link metadata.

    expected_materials: A list of rules to encode expectations about used
        artifacts (see ``rulelib`` for formats).

    expected_products:  A list of rules to encode expectations about produced
        artifacts (see ``rulelib`` for formats).

  """
  name = attr.ib()
  expected_materials = attr.ib()
  expected_products = attr.ib()


  def __init__(self, **kwargs):
    super(SupplyChainItem, self).__init__()
    self.name = kwargs.get("name")
    self.expected_materials = kwargs.get("expected_materials", [])
    self.expected_products = kwargs.get("expected_products", [])


  def __repr__(self):
    """Returns an indented JSON string of the metadata object. """
    return json.dumps(attr.asdict(self),
        indent=1, separators=(",", ": "), sort_keys=True)


  def add_material_rule_from_string(self, rule_string):
    """Parse artifact rule string as list and add to expected_materials.

    Arguments:
      rule_string: An artifact rule string (see ``rulelib`` for formats).

    Raises:
      securesystemslib.exceptions.FormatError: Argument is malformed.

    """
    securesystemslib.schema.AnyString().check_match(rule_string)
    rule_list = shlex.split(rule_string)

    # Raises format error if the parsed rule_string is not a valid rule
    in_toto.rulelib.unpack_rule(rule_list)

    self.expected_materials.append(rule_list)


  def add_product_rule_from_string(self, rule_string):
    """Parse artifact rule string as list and add to expected_products.

    Arguments:
      rule_string: An artifact rule string (see ``rulelib`` for formats).

    Raises:
      securesystemslib.exceptions.FormatError: Argument is malformed.

    """
    securesystemslib.schema.AnyString().check_match(rule_string)
    rule_list = shlex.split(rule_string)

    # Raises format error if the parsed rule_string is not a valid rule
    in_toto.rulelib.unpack_rule(rule_list)

    self.expected_products.append(rule_list)


  def _validate_expected_materials(self):
    """Private method to check that material rules are correctly formed."""
    if not isinstance(self.expected_materials, list):
      raise securesystemslib.exceptions.FormatError(
          "Material rules should be a list!")

    for rule in self.expected_materials:
      in_toto.rulelib.unpack_rule(rule)


  def _validate_expected_products(self):
    """Private method to check that product rules are correctly formed."""
    if not isinstance(self.expected_products, list):
      raise securesystemslib.exceptions.FormatError(
          "Product rules should be a list!")

    for rule in self.expected_products:
      in_toto.rulelib.unpack_rule(rule)



@attr.s(repr=False, init=False)
class Step(SupplyChainItem):
  """A step of a software supply chain.

  A Step object is usually contained in a Layout object and encodes the
  expectations for a step of the software supply chain such as, who is
  authorized to perform the step, what command is executed, and which artifacts
  are used and produced. Evidence about a performed step is provided by link
  metadata.

  Attributes:
    pubkeys: A list of functionary keyids authorized to perform the step.

    threshold: A minimum number of distinct functionaries required to provide
        evidence for a step.

    expected_command: A list of command and command arguments, expected to
        perform the step.

  """
  _type = attr.ib()
  pubkeys = attr.ib()
  expected_command = attr.ib()
  threshold = attr.ib()


  def __init__(self, **kwargs):
    super(Step, self).__init__(**kwargs)
    self._type = "step"
    self.pubkeys = kwargs.get("pubkeys", [])
    self.expected_command = kwargs.get("expected_command", [])
    self.threshold = kwargs.get("threshold", 1)

    self.validate()


  @staticmethod
  def read(data):
    """Creates a Step object from its dictionary representation.

    Arguments:
      data: A dictionary with step metadata fields.

    Raises:
      securesystemslib.exceptions.FormatError: Passed data is invalid.

    Returns:
      The created Step object.

    """
    return Step(**data)


  def set_expected_command_from_string(self, command_string):
    """Parse command string as list and assign to expected_command.

    Arguments:
      command_string: A command and command arguments string.

    Raises:
      securesystemslib.exceptions.FormatError: Argument is malformed.

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
    if not isinstance(self.threshold, int):
      raise securesystemslib.exceptions.FormatError(
          "Invalid threshold '{}', value must be an int."
          .format(self.threshold))


  def _validate_pubkeys(self):
    """Private method to check that the pubkeys is a list of keyids."""
    if not isinstance(self.pubkeys, list):
      raise securesystemslib.exceptions.FormatError(
          "The pubkeys field should be a list!")

    for keyid in self.pubkeys:
      securesystemslib.formats.KEYID_SCHEMA.check_match(keyid)


  def _validate_expected_command(self):
    """Private method to check that the expected_command is proper."""
    if not isinstance(self.expected_command, list):
      raise securesystemslib.exceptions.FormatError(
          "The expected command field is malformed!")



@attr.s(repr=False, init=False)
class Inspection(SupplyChainItem):
  """An inspection for a software supply chain.

  An Inspection object is usually contained in a Layout object and encodes a
  command to be executed by an in-toto client during final product
  verification. Akin to steps, inspections can define artifact rules.

  Attributes:
    run: A list of command and command arguments to be executed upon final
        product verification.

  """
  _type = attr.ib()
  run = attr.ib()


  def __init__(self, **kwargs):
    super(Inspection, self).__init__(**kwargs)
    self._type = "inspection"
    self.run = kwargs.get("run", [])

    self.validate()


  @staticmethod
  def read(data):
    """Creates an Inspection object from its dictionary representation.

    Arguments:
      data: A dictionary with inspection metadata fields.

    Raises:
      securesystemslib.exceptions.FormatError: Passed data is invalid.

    Returns:
      The created Inspection object.

    """
    return Inspection(**data)


  def set_run_from_string(self, command_string):
    """Parse command string as list and assign to run attribute.

    Arguments:
      command_string: A command and command arguments string.

    Raises:
      securesystemslib.exceptions.FormatError: Argument is malformed.

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
    if not isinstance(self.run, list):
      raise securesystemslib.exceptions.FormatError(
          "The run field is malformed!")
