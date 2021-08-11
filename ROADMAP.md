Roadmap
=======

_Note: Previous roadmaps can be found with the roadmap reviews for that period.
[Link to Roadmap 2021](roadmap-reviews/2021/ROADMAP.md)_

This document spans the Roadmap for the in-toto main implementation for the
time window from August 2021 to August 2022. The main focus of this year is to
adopt all the new and exciting features that are taking place in the ITE space:

- ITE-4: Support abstract artifact resource types (more on this below)
- ITE-5: Use a new, and pluggable signing specification
- ITE-6: Support abstract link attestation types (e.g., vulnerability scan)
- ITE-7: Support external identity providers for functionaries (e.g., x509 or SPIFFE)

That is, we envision that many of these features will slowly take place within
the reference implementation to provide features that the community wants. 

## First class ITE support

The previous years's roadmap aimed to culminate with in-toto's 1.0
release, as we aimed to provide stability for our implementors. In contrast,
this year has been filled with excitement and new energy on the software supply
chain security space. We are very excited to work with more sister projects
that aim to provide new ways to further protect the software supply chain
(Shout out to Sigstore, Keylime, SPIFFE, and many others!)

As such, we have spent a large part of the previous roadmap brianstorming and
devising new elements of the in-toto spec. This being a reference
impelementation, we will ensure we can provide these new, exciting features
once they are mature enough.

### ITE-4: abstract resource types

A perhaps already established is ITE is ITE-4, which focuses on abstract
resources. This is paramount for some uses, such as the CNAB security
specification. In this case, we will be adding facilities for custom artifact
hashers/resolvers. We also envision providing some baseline catalog of these
hashers for common usecases so that people have something to reference when
writing their own and --- of course --- use them.

This year, we will spend time providing interfaces for the end-user tooling to
simplify hashing and resolving of abstract resource types. Naturally, this will
also come with human-related efforts to ensure the community can provide their
own hashers/resolvers for these types.

### ITE-5: The move to DSSE (and other wrappers)

A common pain point with implementers is our TUF-based metablock signing
envelope. Although it's been around for a while (maybe more than ten years?!),
it seems that that the ecosystem has grown around this particular space.
Players like JWT (and the whole JOSE suite), COSE (for CBOR), PASETO and DSSE
have surfaced as standalone and mature signing envelope specifications. Working
with the community, we have developed ways to support new singing envelopes in
golang, and we expect to provide a backwards-compatible way to sign and verify
DSSE-based in-toto metadata in a new release of in-toto. Whether this will
warrant a major version bump is yet to be decided.

### ITE-6: Abstract link metadata types

When we first designed in-toto, we expected links to be opaque descriptors that
could represent yet-to-be-known supply chain attestation types. As the
ecosystem has matured (it's been almost half a decade since the first commit!),
it appears that more expressive, ad-hoc types will simplify both
policy-writing, as well as inspection engines and more.

The previous cycle we worked closely with various people to come up with the
[attestations](https://github.com/in-toto/attestation) repository. This
describes various ways to represent common supply chain steps (e.g., building,
scanning for CVEs, or even compiling a software bill of materials). Although
old links are here to stay (and will still suffice for yet-to-be-known supply
chain steps), we will put in place facilities that allow us to *create* these
attestations. Likewise, we expect movement in the policy (layout) side of
things --- what use is to create attestations if we can't verify them?

### ITE-7: Leveraging further identity provider ecosystems.

Many software ecosystems have mature identity provider ecosystems in place
(think of the GPG ecosystem in the linux distribution world, or x509
certificate chains for private infrastructure). We expect this ITE to provide
building blocks for tools like SPIFFE or Sigstore's Fulcio to create
functionary identification information that can be used to enroll them in
in-toto layouts. This will allow for a tighter integration betwee in-toto and
existing software pipelines, as well as the use of ephemeral worker keys (e.g.,
by using SPIFFE) for short-lived supply chain workers. We expect this ITE to
come around through this year (more on it on the organizational roadmap), and
we expect to provide early implementations of this by the third review period.

## Measured supply chain execution using Keylime

Although this is in very early stages of development, we hope to work closely
with the keylime project to provide pathways to embed keylime TPM-ME
metainformation in ITE-6 metadata. This will raise the bar about the integrity
of a running host. The inclusion of trusted hardware semantics in the in-toto
ecosystem is something we have been hoping to see for a while now.

## CII Gold badge

Last year we fell slightly short of our Gold badge goal. This year we will tick
the missing boxes, and finally meet the gold standard (pun intended) on secure
development practices.

## Release scheduling and roadmap review schedule

This year we intend to continue our release schedule. This includes a more
formal Service Level Agreement considering a four-month window between minor
versions.

- Months 1-2: Normal development. Including new features, refactoring, and bugfixes.
- Month 3: Feature freeze. Only bugfixes and security vulnerabilities are allowed.
- Month 4: Release candidate period. A new version is released by the end of
  the fourth month.

This schedule will roughly match the following months:

- [End of December](roadmap-reviews/2021/review_1_december_20.md)
- [End of April](roadmap-reviews/2021/review_2_april_21.md)
- End of July

These time windows will also be used to review and update all stakeholders with
the status of the in-toto implementation.
