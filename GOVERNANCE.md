# in-toto governance
This document covers the project's governance and committer process.  The
project consists of the in-toto
[specification](https://github.com/in-toto/docs) and
[reference implementation](https://github.com/in-toto/in-toto).

## Maintainership and Consensus Builder
The project is maintained by the people indicated in
[MAINTAINERS.txt](MAINTAINERS.txt).  A maintainer is expected to (1) submit and
review GitHub pull requests and (2) open issues or [submit vulnerability
reports](https://github.com/in-toto/in-toto#security-issues-and-bugs).
A maintainer has the authority to approve or reject pull requests submitted by
contributors.  The project's Consensus Builder (CB) is
Justin Cappos <jcappos@nyu.edu, @JustinCappos>.

## Contributions
A contributor can submit GitHub pull requests to the project's repositories.
They must follow the project's [code of
conduct](CODE-OF-CONDUCT.md), the [Developer Certificate of
Origin (DCO)](https://developercertificate.org/) and the [code style
guidelines](https://github.com/secure-systems-lab/code-style-guidelines), and
they must unit test any new software feature or change.  Submitted pull
requests undergo review and automated testing, including, but not limited to:

* Unit and build testing via [Tox](https://tox.readthedocs.io/en/latest/) on
[GitHub Actions](https://github.com/in-toto/in-toto/actions) and
[AppVeyor](https://ci.appveyor.com/project/in-toto/in-toto)
* Static code analysis via [Pylint](https://www.pylint.org/) and
[Bandit](https://wiki.openstack.org/wiki/Security/Projects/Bandit)
* Checks for *Signed-off-by* commits via [Probot: DCO](https://probot.github.io/apps/dco/)
* Review by one or more [maintainers](MAINTAINERS.txt)

See [*Instructions for
Contributors*](https://github.com/in-toto/in-toto#instructions-for-contributors)
for help.

## Changes in maintainership

A contributor to the project must express interest in becoming a maintainer.
The CB has the authority to add or remove maintainers.

## Changes in governance
The CB supervises changes in governance.