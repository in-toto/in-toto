# ROADMAP review (End of July '21)

We've reached the end of our third and final evaluation period of our [roadmap for
2021](https://github.com/in-toto/in-toto/blob/develop/roadmap-reviews/2021/ROADMAP.md)
and it is time to do a review of how the in-toto reference implementation is
holding up to its goals for this year. In this document, we will cover the
activities from May to June 2021 in the context of the goals for this
ROADMAP as well as other newsworthy developments.


## Releases

We released version 1.1.1 of the reference implementation which included some
dependency updates and other enhancements like new tests for `match` rules and
code quality improvements based on linter recommendations. This was primarily a
stability and quality-of-life update, but we are also glad to have a new external
contributor submit patches!

###  Relevant documents

- 1.1.1 release (on [PyPI](https://pypi.org/project/in-toto/v1.1.1)
  and on [GitHub](https://github.com/in-toto/in-toto/releases/tag/v1.1.1))
  - Closed issues and merged pull requests
    - Added tests that use source and destination prefixes in match rules,
      courtesy of Brandon Michael Hunter
      ([#456](https://github.com/in-toto/in-toto/pull/456))
    - Updated documentation of command alignment during verification workflow
      ([#455](https://github.com/in-toto/in-toto/pull/455))
    - Started using GitHub-native dependabot
      ([#450](https://github.com/in-toto/in-toto/pull/450))
    - Bump dependencies:
      attrs ([#451](https://github.com/in-toto/in-toto/pull/451)),
      six ([#452](https://github.com/in-toto/in-toto/pull/452)),
      securesystemslib ([#453](https://github.com/in-toto/in-toto/pull/453)),
      cffi ([#457](https://github.com/in-toto/in-toto/pull/457)),
      python-dateutil ([#458](https://github.com/in-toto/in-toto/pull/458)),
      iso8601 ([#459](https://github.com/in-toto/in-toto/pull/459)),
      pathspec ([#460](https://github.com/in-toto/in-toto/pull/460))
    - Fixed linter warnings
      ([#462](https://github.com/in-toto/in-toto/pull/462))

## Verifying in-toto with in-toto

After Yuanrui Chen's excellent work putting together a layout for in-toto
releases, the focus has shifted to distributing the layout in a secure way,
using our sister project TUF. While this is a work in progress, we expect
the final result to leverage the TUF + in-toto pipeline detailed in ITE-2
and ITE-3.

### Relevant documents

- Pull request for verifying in-toto's supply chain with in-toto
  ([#444](https://github.com/in-toto/in-toto/pull/444))
- Issue for verifying in-toto's supply chain with in-toto
  ([#278](https://github.com/in-toto/in-toto/issues/278))
- [ITE-2](https://github.com/in-toto/ITE/blob/master/ITE/2/README.adoc)
- [ITl-3](https://github.com/in-toto/ITE/blob/master/ITE/3/README.adoc)

## ITEs

While [ITE-5](https://github.com/in-toto/ITE/blob/master/ITE/5/README.adoc)
is still a draft, the signature wrapper it recommends, the Dead Simple Signing
Envelope (DSSE) has reached v1.0. Discussions continue to enhance the
specification, which was previously known as the SSL Signing Spec.

While the specification ships with a lightweight Python implementation, the
eventual plan is to integrate that into our crypto-backend, securesystemslib,
enabling the reference implementation to transition over to the new wrapper.

Further, [ITE-6](https://github.com/in-toto/ITE/blob/master/ITE/6) has been
merged as a draft, and the discussions have continued in the in-toto Attestations
[repository](https://github.com/in-toto/attestation). More information will be
coming soon on this front.

## CII Gold Badge

Unfortunately, this is a goal we have not been able to meet this period, yet we
are incredibly close -- 86% of the way through!. The reference implementation
closely matches the current release of the in-toto specification, and as a
result, active development has slowed down. This has led to us not meeting one
major criteria in the defined time period: having two unassociated significant
contributors. As ITE-5 and ITE-6 materialize, we believe we will have the
necessary activity to apply for the Gold badge.

### Relevant documents

- in-toto's page on the CII Best Practices
  [Badge App](https://bestpractices.coreinfrastructure.org/en/projects/1523?criteria_level=2)

## Closing remarks.

in-toto's reference implementation has been stable for some time now, and we
are very excited to continue working on new ideas and features that can help
secure software supply chains. Among other things, we are excited to work on
adding support for ITE-5, i.e., enabling new signing specifications, and our
work on in-toto Attestations through ITE-6.
