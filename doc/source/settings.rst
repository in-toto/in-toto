Settings
========

Default values for these settings are defined in the `in_toto.settings
<https://github.com/in-toto/in-toto/blob/develop/in_toto/settings.py>`_ module.
Settings names are case sensitive and settings values that contain colons are
parsed as list.

.. note::
  The default ``in_toto.settings`` are used unless overridden via API function
  arguments or, in the case of CLI usage, via CLI arguments.


Setting Types
-------------

- ``ARTIFACT_EXCLUDE_PATTERNS`` -- gitignore-style paths patterns exclude
  artifacts from being recorded.
- ``ARTIFACT_BASE_PATH`` -- material and product paths passed to
  ``in-toto-run`` are searched relative to the base path. The base path itself
  is not included in the link metadata. Default is the current working
  directory.
- ``LINK_CMD_EXEC_TIMEOUT`` -- maximum timeout setting for the in-toto-run
  command.
