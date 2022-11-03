# in-toto governance
This document covers the project's governance and committer process.  The
project consists of the in-toto
[specification](https://github.com/in-toto/docs) and
[reference implementation](https://github.com/in-toto/in-toto).

## Code of Conduct

The in-toto community abides by the Cloud Native Computing Foundation's [code of conduct](/CODE-OF-CONDUCT.md). An excerpt follows:

> _As contributors and maintainers of this project, and in the interest of fostering an open and
> welcoming community, we pledge to respect all people who contribute through reporting issues,
> posting feature requests, updating documentation, submitting pull requests or patches, and other
> activities._

in-toto community members represent the project and their fellow contributors. We value our 
community tremendously, and we'd like to keep cultivating a friendly and collaborative environment 
for our contributors and users. We want everyone in the community to have a positive experience.


## Maintainership and Consensus Builder
The project is maintained by the people indicated in
[MAINTAINERS.txt](MAINTAINERS.txt).  A maintainer is expected to (1) submit and
review GitHub pull requests and (2) open issues or [submit vulnerability
reports](https://github.com/in-toto/in-toto#security-issues-and-bugs).
A maintainer has the authority to approve or reject pull requests submitted by
contributors.  Any maintainer may also interact with the CNCF on behalf of the
project.  

The project's Consensus Builder (CB), who is also granted all maintainer 
privileges and responsibilities, is Santiago Torres-Arias 
<santiagotorres@purdue.edu, @SantiagoTorres>.


## Reference Implementation Contributions
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

## Specification changes (ITEs) 
The [in-toto enhancement (ITE)](https://github.com/in-toto/ITE) approval process which 
changes the in-toto specification is listed in 
[ITE-1](https://github.com/in-toto/ITE/blob/master/ITE/1/README.adoc_).  Future
changes in the ITE process will be managed through new ITEs.

## Changes in maintainership
Active contributors may be offered or request to be granted maintainer status.
This requires approval from the CB and is done in consultation with the
current maintainers.

Maintainers may be moved to emeritus status.  This is done at the discretion of 
the CB, in consultation with the project maintainers.  Emeritus maintainers are 
listed in the MAINTAINERS.txt file as acknowledgment for their prior service to 
the project, but no longer have code review or other maintainer privileges for 
the project.

## Changes in governance
The CB supervises changes in governance, in consultation with project maintainers.
