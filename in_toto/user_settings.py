"""
<Program Name>
  user_settings.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Oct 25, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides methods to parse environment variables (`get_env`) and RCfiles
  (`get_rc`) and to override default settings (`set_settings`) defined in the
  `in_toto.settings` module.

  Check out the respective docstrings to learn about the requirements for
  environment variables and RCfiles (includes examples).

"""
import os
import six
import logging
import in_toto.settings

try:
  import configparser
except ImportError: # pragma: no cover
  import ConfigParser as configparser

# Inherits from in_toto base logger (c.f. in_toto.log)
LOG = logging.getLogger(__name__)


USER_PATH = os.path.expanduser("~")

# Prefix required by environment variables to be considered as in_toto settings
ENV_PREFIX = "IN_TOTO_"

# List of considered rcfile paths in the order they get parsed and overridden,
# i.e. the same setting in `/etc/in_toto/config` and `.in_totorc` (cwd) uses
# the latter
RC_PATHS = [
  os.path.join("/etc", "in_toto", "config"),
  os.path.join("/etc", "in_totorc"),
  os.path.join(USER_PATH, ".config", "in_toto", "config"),
  os.path.join(USER_PATH, ".config", "in_toto"),
  os.path.join(USER_PATH, ".in_toto", "config"),
  os.path.join(USER_PATH, ".in_totorc"),
  ".in_totorc"
]

# List of settings, for which defaults exist in `settings.py`
# TODO: Should we use `dir` on the module instead? If we list them here, we
# have to manually update if `settings.py` changes.
IN_TOTO_SETTINGS = [
  "ARTIFACT_EXCLUDE_PATTERNS", "ARTIFACT_BASE_PATH", "LINK_CMD_EXEC_TIMEOUT"
]


def _colon_split(value):
  """ If `value` contains colons, return a list split at colons,
  return value otherwise. """
  value_list = value.split(":")
  if len(value_list) > 1:
    return value_list

  return value


def get_env():
  """
  <Purpose>
    Parse environment for variables with prefix `ENV_PREFIX` and return
    a dict of key-value pairs.

    The prefix `ENV_PREFIX` is stripped from the keys in the returned dict.

    Values that contain colons (:) are split at the postion of the colons and
    converted into a list.


    Example:

    ```
    # Exporting variables in e.g. bash
    export IN_TOTO_ARTIFACT_BASE_PATH='/home/user/project'
    export IN_TOTO_ARTIFACT_EXCLUDE_PATTERNS='*.link:.gitignore'
    export IN_TOTO_LINK_CMD_EXEC_TIMEOUT='10'
    ```

    produces

    ```
    {
      "ARTIFACT_BASE_PATH": "/home/user/project"
      "ARTIFACT_EXCLUDE_PATTERNS": ["*.link", ".gitignore"]
      "LINK_CMD_EXEC_TIMEOUT": "10"
    }
    ```

  <Exceptions>
    None.

  <Side Effects>
    Calls function to read files from disk.

  <Returns>
    A dictionary containing the parsed key-value pairs.

  """
  env_dict = {}

  for name, value in six.iteritems(os.environ):
    if (name.startswith(ENV_PREFIX) and
        len(name) > len(ENV_PREFIX)):
      stripped_name = name[len(ENV_PREFIX):]

      env_dict[stripped_name] = _colon_split(value)

  return env_dict


def get_rc():
  """
  <Purpose>
    Reads RCfiles from the paths defined in `RC_PATHS` and returns
    a dictionary with all parsed key-value pairs.

    The RCfile format is as expected by Python's builtin `ConfigParser` with
    the addition that values that contain colons (:) are split at the position
    of the colons and converted into a list.

    Section titles in RCfiles are ignored when parsing the key-value pairs.
    However, there has to be at least one section defined.

    The paths in `RC_PATHS` are ordered in reverse precedence, i.e. each file's
    settings override a previous file's settings, e.g. a setting defined
    in `.in_totorc` (in the current working dir) overrides the same
    setting defined in `~/.in_totorc` (in the user's home dir) and so on ...

    Example:

    ```
    # E.g. file `.in_totorc` in current working directory
    [in-toto setting]
    ARTIFACT_BASE_PATH = /home/user/project
    ARTIFACT_EXCLUDE_PATTERNS = *.link:.gitignore
    LINK_CMD_EXEC_TIMEOUT = 10
    ```

    produces

    ```
    {
      "ARTIFACT_BASE_PATH": "/home/user/project"
      "ARTIFACT_EXCLUDE_PATTERNS": ["*.link", ".gitignore"]
      "LINK_CMD_EXEC_TIMEOUT": "10"
    }
    ```

  <Exceptions>
    None.

  <Side Effects>
    Calls function to read files from disk.

  <Returns>
    A dictionary containing the parsed key-value pairs.

  """
  rc_dict = {}

  config = configparser.ConfigParser()
  # Reset `optionxform`'s default case conversion to enable case-sensitivity
  config.optionxform = str
  config.read(RC_PATHS)

  for section in config.sections():
    for name, value in config.items(section):
      rc_dict[name] = _colon_split(value)

  return rc_dict


def set_settings():
  """
  <Purpose>
    Calls functions that read in-toto related environment variables and RCfiles
    and overrides variables in `settings.py` with the retrieved values, if they
    are whitelisted in `IN_TOTO_SETTINGS`.

    Settings defined in RCfiles take precedence over settings defined in
    environment variables.

  <Exceptions>
    None.

  <Side Effects>
    Calls functions that read environment variables and files from disk.

  <Returns>
    None.

  """
  user_settings = get_env()
  user_settings.update(get_rc())

  # If the user has specified one of the settings whitelisted in
  # IN_TOTO_SETTINGS per envvar or rcfile, override the item in `settings.py`
  for setting in IN_TOTO_SETTINGS:
    user_setting = user_settings.get(setting)
    if user_setting:
      LOG.info("Setting (user): {0}={1}".format(
          setting, user_setting))
      setattr(in_toto.settings, setting, user_setting)

    else:
      default_setting = getattr(in_toto.settings, setting)
      LOG.info("Setting (default): {0}={1}".format(
          setting, default_setting))
