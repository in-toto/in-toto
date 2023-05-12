# in-toto Governance

in-toto's
[governance](https://github.com/in-toto/community/blob/main/GOVERNANCE.md) and
[code of conduct](https://github.com/in-toto/community/blob/main/CODE-OF-CONDUCT.md)
are described in the [in-toto/community](https://github.com/in-toto/community)
repository.

## Reference Implementation Contributions

This implementation adheres to
[in-toto's contributing guidelines](https://github.com/in-toto/community/blob/main/CONTRIBUTING.md).
Pull requests must be submitted to the `develop` branch where they undergo
review and automated testing, including, but not limited to:
* Unit and build testing via [Tox](https://tox.readthedocs.io/en/latest/) on
  [GitHub Actions](https://github.com/in-toto/in-toto/actions)
* Static code analysis via [Pylint](https://www.pylint.org/) and
  [Bandit](https://wiki.openstack.org/wiki/Security/Projects/Bandit)
* Checks for *Signed-off-by* commits via
  [Probot: DCO](https://probot.github.io/apps/dco/)
* Review by one or more [maintainers](MAINTAINERS.txt)
