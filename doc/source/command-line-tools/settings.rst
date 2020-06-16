Settings
========

For historical reasons some command line options may also be configured via
rcfiles in one of the following locations *.in_totorc*, *~/.in_totorc*,
*~/.in_toto/config*, *~/.config/in_toto*, *~/.config/in_toto/config*,
*/etc/in_totorc*, */etc/in_toto/config* or via environment variables in above
presented order of precedence.

Default values for these settings are defined in the `in_toto.settings
<https://github.com/in-toto/in-toto/blob/develop/in_toto/settings.py>`_ module.
Settings names are case sensitive and settings values that contain colons are
parsed as list.

Setting Types
-------------

- ``ARTIFACT_EXCLUDE_PATTERNS`` -- gitignore-style paths patterns exclude
  artifacts from being recorded.
- ``ARTIFACT_BASE_PATH`` -- material and product paths passed to
  ``in-toto-run`` are searched relative to the base path. The base path itself
  is not included in the link metadata. Default is the current working
  directory.


Example Usage
-------------

.. code-block:: sh

  # Configure settings via bash-style environment variable export
  export IN_TOTO_ARTIFACT_BASE_PATH='/home/user/project'
  export IN_TOTO_ARTIFACT_EXCLUDE_PATTERNS='*.link:.gitignore'

.. code-block:: sh

  # Configure settings via ~/.in_totorc
  [in-toto settings]
  ARTIFACT_BASE_PATH=/home/user/project
  ARTIFACT_EXCLUDE_PATTERNS=*.link:.gitignore
