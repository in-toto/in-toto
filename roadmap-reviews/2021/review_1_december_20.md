# ROADMAP review (End of December '20)

We're past the first evaluation period of our [roadmap for
2021](https://github.com/in-toto/in-toto/blob/develop/roadmap-reviews/2021/ROADMAP.md) and it is
time to do a review of how the in-toto reference implementation is
holding up to its goals for this year. In this document, we will cover the
activities from August to December 2020 in the context of the goals for this
ROADMAP as well as other newsworthy developments.


## Release of 1.0.0

Our main objective of last year's roadmap was to tie down the public API for a
1.0.0 release. While we successfully revised the better part of the in-toto
interface and corresponding documentation, one remaining issue spilled over
into the 2021 roadmap, that is a clean-up of the utility and keys module (see
[previous roadmap review](roadmap-reviews/2020/review_3_june_20.md)). Thus, we
are all the more excited to announce that during this first 2021 roadmap review
period we were able to sort out that remaining issue and publish in-toto 1.0.0.

Compared to the previous version 0.5.0, which we published last fall, in-toto
1.0.0 includes better API and usage documentation, a more intuitive interface
to handle cryptographic keys, and a few useful small features (the
[CHANGELOG](https://github.com/in-toto/in-toto/blob/develop/CHANGELOG.md) has
the details). But above all, it is a commitment to the maturity and stability
of the in-toto reference implementation.

###  Relevant documents

- 1.0.0 release (on [PyPI](https://pypi.org/project/in-toto/v1.0.0)
  and on [GitHub](https://github.com/in-toto/in-toto/releases/tag/v1.0.0))
- [in-toto.readthedocs.io](https://in-toto.readthedocs.io/en/latest/) (official docs)
- Closed issues and merged pull requests
  - Stable API ([#277](https://github.com/in-toto/in-toto/issues/80))
  - Replace utility module with revised securesystemslib key interface
    ([#80](https://github.com/in-toto/in-toto/issues/80),
    [#402](https://github.com/in-toto/in-toto/pull/402))
  - Update securesystemslib key interface
    ([sslib#288](https://github.com/secure-systems-lab/securesystemslib/pull/288),
    [sslib#278](https://github.com/secure-systems-lab/securesystemslib/pull/278),
    [sslib#276](https://github.com/secure-systems-lab/securesystemslib/pull/276))
  - Strengthen securesystemslib key interface tests
    ([sslib#287](https://github.com/secure-systems-lab/securesystemslib/pull/287),
    [sslib#279](https://github.com/secure-systems-lab/securesystemslib/pull/279))

## New ITE compliance

Mark Lodato (@MarkLodato) and his Binary Authorization team at Google are
championing two new ITEs that generalize the in-toto link format
([ITE-6](https://github.com/in-toto/ITE/pull/15/)) and the metadata signature
wrapper shared with the TUF implementation
([ITE-5](https://github.com/in-toto/ITE/pull/13)). The latter has become the
corner stone for a new singing specification to be shared with the in-toto
sister project TUF (see recent [organization roadmap
review](https://github.com/in-toto/docs/tree/master/roadmap-reviews/2020) for
details).

To leverage this momentum we are revising our in-house crypto library
securesystemslib, which will become the reference implementation for the new
signing specification, and have created a GitHub milestone that gathers issues
on the path towards version 1.0.0. This milestone includes similar items as we
had for in-toto 1.0.0, such as a clear definition of the stable API plus
corresponding documentation overhaul. In addition, we are adding more
flexibility on signing implementations by adding an abstract signing interface,
and have explored minor inconsistencies in cryptographic key formats which we
aim to consolidate.


### Relevant documents
- [Signing Specification](https://github.com/secure-systems-lab/signing-spec)
- [securesystemslib 1.0.0 milestone](https://github.com/secure-systems-lab/securesystemslib/milestone/1)
- Revise architecture for stable API ([sslib#270](https://github.com/secure-systems-lab/securesystemslib/issues/270))
- Overhaul docs ([sslib#271](https://github.com/secure-systems-lab/securesystemslib/issues/271))
- Consolidate key formats ([sslib#251](https://github.com/secure-systems-lab/securesystemslib/issues/251))
  - public key metadata format ([sslib#308](https://github.com/secure-systems-lab/securesystemslib/issues/308))
  - stand-alone on-disk key format ([sslib#309](https://github.com/secure-systems-lab/securesystemslib/issues/309))
  - in-memory key representation ([sslib#310](https://github.com/secure-systems-lab/securesystemslib/issues/310))
- Abstract signing interface ([tuf#1263](https://github.com/theupdateframework/tuf/issues/1263))


## Tangential work

A key requirement for our reference implementation is its readability. This
both helps integrators to adopt our concepts, and, as we believe, also has a
strong positive impact on the security, correctness, and robustness of the
software. On these grounds we have spent great efforts on revamping our [code
style guide](https://github.com/secure-systems-lab/code-style-guidelines/blob/master/python.md)
to align with current best practices in Python software development.

And as good open source citizens we have upstreamed a feature for the Sphinx
doc tool that enhances custom API documentation as prescribed by our new style
guide. Kudos to our student assistant Yuanrui Chen (@SolidifiedRay), who
spear-headed that development.

### Relevant documents
- Update code style guide  ([sslab#21](https://github.com/secure-systems-lab/code-style-guidelines/pull/21))
- Further customize Napoleon Sphinx custom sections ([sphinx#8658](https://github.com/sphinx-doc/sphinx/pull/8658))

## Closing remarks.

Given the solid foundation that we have built with in-toto 1.0.0, we can now,
with good conscience, explore new ideas and experiment with new features. As
indicated in the 2021 roadmap, this will first and foremost include the
implementation of custom ITE-4 artifact resolvers.

In parallel we will push forward the realization of the designs for an
enhanced Secure Systems Lab signature wrapper for in-toto and TUF as discussed
in ITE-5.

And last but not least we will continue to tighten the development and release
procedures for the project, with the goal of earning the CII best practice gold
badge.
