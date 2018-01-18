# Changelog

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
