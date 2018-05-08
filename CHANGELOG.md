# Changelog

## in-toto v0.2.2

* Add support for gpg signing subkeys.
* Drop strict requirement on securesystemslib 0.10.
* Command line tool changes:
    - Add a --base-path parameter to in-toto record and in-toto run
    - in-toto-record now follows symbolic links
* Fixed typo in exception messages
* Adds support for sublayout namespacing (for in-toto spec 0.9 compliance)
* Path prefix is normalized during in-toto verification:
    - Paths such as foo//bar match with foo/bar.
* Dropped obsolete SettingsError


## in-toto v0.2.1

* Model changes
  - Add metablock validators
  - Add abstract class for layout steps and inspections
  - Disallow passing command string to step and inspection constructor
  - Add custom `__repr__` for step and inspection objects
  - Add layout creation convenience methods
* Command Line tool changes
  - Add missing shebangs
  - Enhance help messages
  - Fix argparse bug for required subcommand in in-toto-record
  - Rename short option to record streams in in-toto-run
* Fix gpg hashing algorithm name
* Add layout creation example document
* Refactor logging and user feedback
* Rename artifact_rules module to rulelib and add convenience methods


## in-toto v0.2.0

* Fix link metadata bug in in_toto_mock
* Add support for GPG signing and verification of layout and link metadata
* Add support for Python 3.4, 3.5 and 3.6
* Refactor signature and threshold verification in final product verification
  so that not every signature on a given layout needs to be valid, as long as
  every signature for which a key is passed is valid, and at least one key is
  passed. Furthermore, not all imported links need need to carry an authorized
  and valid signature, as as long as there are enough links with an authorized
  and valid signature for any given step. Links with unauthorized signatures or
  invalid signatures are ignored
* Remove canonicaljson dependency and use securesystemslib's canonicaljson
  encoding
* Refactor order of positional arguments in in-toto-record command line tool
* Add linters (pylint and bandit) and fix linting errors (e.g.: indentation
  and unused variables and imports)
* Add schemas for in-toto specific crypto-related metadata formats
* Improve testing code coverage to 100%
* Add debian directory required to create a debian package
* Add .editorconfig and GitHub issue and pull request templates,
  ACKNOWLEDGEMENTS.md, CODE-OF-CONDUCT.md, GOVERNANCE.md, MAINTAINERS.txt and
  passing core infrastructure best practice badge, add "Security Issues and
  Bugs" and "Instructions for Contributors" section in README.md


## in-toto v0.1.1
* Initial pre-release
