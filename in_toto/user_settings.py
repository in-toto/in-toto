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
  Provides methods to read environment variables and rcfiles and to write
  them to the in_toto.settings module (override them) if whitelisted.

  Notes:
  - Variable values are converted to lists if they contain colons
  - Variable names are converted to upper case
  - Environment variables need to be prefixed with "IN_TOTO_". The prefix is
    removed when the variable is written to the settings module,
    e.g. the envvar...
    IN_TOTO_ARTIFACT_EXCLUDES="*.link:.gitignore"

    becomes the setting ...
    in_toto.settings.ARTIFACT_EXCLUDES = ["*.link", ".gitignore"]

  - RCfile values follow the format expected by Python's builtin
    ConfigParser. The format requires at least one section, sections however
    are ignored, e.g. the rcfile...
    [ignored section name]
    artifact_basepath = "/a/b/c"

    becomes the setting ...
    in_toto.settings.ARTIFACT_BASEPATH = "/a/b/c"

  - Order of precedence
    1. RCfiles
        .in_totorc
        ~/.in_totorc
        ~/.in_toto/config
        ~/.config/in_toto
        ~/.config/in_toto/config
        /etc/in_totorc
        /etc/in_toto/config
    2. Environment Variables
    3. Settings defined in `settings.py`

"""
import os
import log
import ConfigParser
import in_toto.settings



USER_PATH = os.path.expanduser("~")

# Prefix required by environment variables to be considered as in_toto settings
ENV_PREFIX = "IN_TOTO_"

# List of considered rcfile paths in the order they get parsed and overridden,
# i.e. the same setting in `/etc/in_toto/config` and `.in_totorc` (cwd) uses
# the latter
RC_PATHS = [
  os.path.join("/etc", "in_toto", "config"),
  os.path.join("/etc", "in_totorc"),
  os.path.join(USER_PATH,  ".config", "in_toto", "config"),
  os.path.join(USER_PATH, ".config", "in_toto"),
  os.path.join(USER_PATH, ".in_toto", "config"),
  os.path.join(USER_PATH, ".in_totorc"),
  ".in_totorc"
]

# List of settings, for which defaults exist in `settings.py`
# TODO: Should we use `dir` on the module instead? If we list them here, we
# have to manually update if settings.py changes.
IN_TOTO_SETTINGS = [
  "ARTIFACT_EXCLUDES", "ARTIFACT_BASE_PATH"
]


def _colon_split(value):
  """ If `value` contains colons, return a list split at colons,
  return value otherwise. """
  value_list = value.split(":")
  if len(value_list) > 1:
    return value_list

  return value


def get_env():
  """Return a dict of environment variables starting with `ENV_PREFIX`

  - In the returned dict the prefix is stripped from the keys
  - Values that contain colons are converted into a list
  - Variable names are converted to upper case

  """
  env_dict = {}

  for name, value in os.environ.iteritems():
    name = name.upper()

    if (name.startswith(ENV_PREFIX) and
        len(name) > len(ENV_PREFIX)):
      stripped_name = name[len(ENV_PREFIX):]

      env_dict[stripped_name] = _colon_split(value)

  return env_dict


def get_rc():
  """Load RCfiles from the usual places and return a dictionary of
  key value pairs.

  - RCfile format as expected by builtin ConfigParser
  - The format dictates that there is at least one section,
    however we are only interested in the values and ignore the sections
  - Values that contain colons are converted into a list
  - Variable names are converted to upper case

  """
  rc_dict = {}

  config = ConfigParser.ConfigParser()
  config.read(RC_PATHS)

  for section in config.sections():
    for name, value in config.items(section):
      name = name.upper()
      rc_dict[name] = _colon_split(value)

  return rc_dict


def set_settings():
  """
  <Purpose>
    Calls functions that read in-toto related environment variables and RCfiles
    and overrides variables `settings.py` with the retrieved values, if they
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
      log.info("Using setting {0}={1}".format(
          setting, user_setting))
      setattr(in_toto.settings, setting, user_setting)
