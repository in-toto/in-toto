# ROADMAP review (End of April '21)

We've reached the end of our second evaluation period of our [roadmap for
2021](https://github.com/in-toto/in-toto/blob/develop/roadmap-reviews/2021/ROADMAP.md) and it is
time to do a review of how the in-toto reference implementation is
holding up to its goals for this year. In this document, we will cover the
activities from January to April 2021 in the context of the goals for this
ROADMAP as well as other newsworthy developments.


## Releases

We followed up the release of 1.0.0 of the reference implementation with a
new patch release, 1.0.1. This is the final release that supports Python 2, as
some of our explicit and transitive dependencies have dropped Python 2 support.
Our next release, 1.1.0, at the end of April 2021, bumped the minor version to
indicate the lack of Python 2 support.

###  Relevant documents

- 1.1.0 release (on [PyPI](https://pypi.org/project/in-toto/v1.1.0)
  and on [GitHub](https://github.com/in-toto/in-toto/releases/tag/v1.1.0))
  - Closed issues and merged pull requests
    - SPDX License identifiers and copyright information
      ([#440](https://github.com/in-toto/in-toto/pull/440))
    - Aditya Sirish (@adityasaky) as a maintainer
      ([#443](https://github.com/in-toto/in-toto/pull/443))
    - PyPI development status from `Beta` to `Production/Stable`
      ([#447](https://github.com/in-toto/in-toto/pull/447))
    - Santiago Torres-Arias's (@SantiagoTorres) email to reflect Purdue
      affiliation ([#446](https://github.com/in-toto/in-toto/pull/446))
    - Debian downstream release metadata
      ([#437](https://github.com/in-toto/in-toto/pull/437))
    - Bump dependency: cryptography
      ([#442](https://github.com/in-toto/in-toto/pull/442))
    - Dropped support for Python 2.7
      ([#438](https://github.com/in-toto/in-toto/pull/438))

- 1.0.1 release (on [PyPI](https://pypi.org/project/in-toto/v1.0.1)
  and on [GitHub](https://github.com/in-toto/in-toto/releases/tag/v1.0.1))
  - Closed issues and merged pull requests
    - Added Python 3.9 to the CI test matrix
      ([#419](https://github.com/in-toto/in-toto/pull/419))
    - Logo and other visual enhancements on readthedocs
      ([#420](https://github.com/in-toto/in-toto/pull/420),
      [#428](https://github.com/in-toto/in-toto/pull/428))
    - Switch to GitHub Actions for CI
      ([#432](https://github.com/in-toto/in-toto/pull/432))
    - Switch to only running bandit on Python versions greater than 3.5
      ([#416](https://github.com/in-toto/in-toto/pull/416))
    - Debian downstream release metadata
      ([#418](https://github.com/in-toto/in-toto/pull/418))
    - Dropped support for Python 3.5
      ([#419](https://github.com/in-toto/in-toto/pull/419))

## Verifying in-toto with in-toto

Yuanrui Chen (@SolidifiedRay) has put together an in-toto layout and a workflow
that enables us to generate in-toto metadata for each release. We hope to use
this workflow as soon as our upcoming release, meaning the users of the
reference implementation can verify the supply chain of each of our releases.

### Relevant documents

- Pull request for verifying in-toto's supply chain with in-toto
  ([#444](https://github.com/in-toto/in-toto/pull/444))
- Issue for verifying in-toto's supply chain with in-toto
  ([#278](https://github.com/in-toto/in-toto/issues/278))

## ITEs

Since our last roadmap review, work on the two in-toto Enhancements (ITEs),
ITE-5 and ITE-6 has progressed.
[ITE-5](https://github.com/in-toto/ITE/blob/master/ITE/5/README.adoc) was
modified from proposing a new signing specification to recommending the use
of the [SSL signing-spec](https://github.com/secure-systems-lab/signing-spec).

[ITE-6](https://github.com/in-toto/ITE/pull/15) is still being actively
discussed and has led to the formation of the in-toto Attestations
[repository](https://github.com/in-toto/attestation). More information will be
coming soon on this front.

## CII Gold Badge

One of our goals for 2021 is to get in-toto the CII Best Practices gold badge.
The reference implementation is currently rated silver, and we have actively
been working on the gold requirements. We raised in-toto's rating to 287 out of
a total of 300. In this evaluation period, we fulfilled criteria such as adding
license information to all source files, verifying all maintainers used the
right type of two factor authentication, added hardening headers to the in-toto
website to meet secure delivery requirements, and more.

### Relevant documents

- in-toto's page on the CII Best Practices
  [Badge App](https://bestpractices.coreinfrastructure.org/en/projects/1523?criteria_level=2)
- Add SPDX and copyright information to source files
  ([#440](https://github.com/in-toto/in-toto/pull/440]))

## Closing remarks.

in-toto's reference implementation has been stable for some time now, and we
are very excited to continue working on new ideas and features that can help
secure software supply chains. Among other things, we are excited to work on
adding support for ITE-5, i.e., enabling new signing specifications. We also
remain optimistic about achieving the CII Best Practices gold badge this year.
