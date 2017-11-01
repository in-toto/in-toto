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
  them to the in_toto.settings module (override them).

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
import ConfigParser
import in_toto.settings

ENV_PREFIX = "IN_TOTO_"
USER = os.path.expanduser("~")

RC_PATHS = [
  os.path.join("/etc", "in_toto", "config"),
  os.path.join("/etc", "in_totorc"),
  os.path.join(USER,  ".config", "in_toto", "config"),
  os.path.join(USER, ".config", "in_toto"),
  os.path.join(USER, ".in_toto", "config"),
  os.path.join(USER, ".in_totorc"),
  ".in_totorc"
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
  """Read environment variables and RCfiles and write them to the
  settings module.
  """
  user_settings = get_env()
  user_settings.update(get_rc())

  for name, value in user_settings.iteritems():
    setattr(in_toto.settings, name, value)
