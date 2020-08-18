Roadmap
=======

This document spans the Roadmap for the in-toto main implementation for the
time window from April 2019 to April 2020. The main theme of this year's
efforts are focused on two fronts strengthening our release process and aiming
for version 1.0!

## Strengthening the release process

As a software supply chain security product, in-toto aims to be at the
forefront of best practices when it comes to developing the tool. As such,
in-toto has the following goals for this year:

### CII Silver badge

in-toto is already marked as "passing criteria" under the Core Infrastructure
Initiative best practices badge. This year we aim to upgrade our rating to
Silver. To work towards this goal, we'll review and comply with the few
missing requirements for the silver badge.

### Thorough documentation of release process with in-toto metadata

We plan on documenting our release process more thoroughly. For this, we also
intend to add in-toto metadata to all of our releases to ensure that all the
practices outlined in the document were followed. This document will include
instructions on how to verify the provided in-toto metadata as you update
in-toto.

## Working towards 1.0

in-toto is integrated in different products already, which is a strong
motivation to hit the 1.0 milestone. This year we intend to reach our 1.0
release.

### The 1.0 milestone

A GitHub project will be announced with the tasks required for the 1.0
milestone by the in-toto team leaders. This milestone will center towards the
reaching of 1) a stable API for the library and the CLI, 2) a thorough
documentation of such API, and 3) specification and ITE compliance.

#### Stable API

The current API for interacting with the in-toto CLI and its library hasn't
changed much, yet there are no guarantees of this happening. During this year
we'll revisit the API definition and settle for a well-defined user-facing
interface for metadata operations, key creation/loading/usage and verification.


#### Documentation

With a well-defined API, it's possible to present more thorough documentation
on how to use in-toto. This year we'll announce more complete documentation
using sphinx and host it on readthedocs.

#### Specification and ITE compliance

This year we'll focus our development efforts on making sure that the
specification and the Python implementation matches to the point. There are
very minor details that drift from both parts.

As part of this effort, we'll also delineate properly what is strictly part of
spec-compliance and what are specification-specific extensions.

## Release scheduling and roadmap review schedule

As part of the 1.0 efforts, we intend to follow a more thorough release
schedule. This includes a more formal Service Level Agreement considering a
four-month window between minor versions.

- Months 1-2: Normal development. Including new features, refactoring, and bugfixes.
- Month 3: Feature freeze. Only bugfixes and security vulnerabilities are allowed.
- Month 4: Release candidate period. A new version is released by the end of
  the fourth month.

This schedule will roughly match the following months:

- [End of August](roadmap-reviews/2020/review_1_august_19.md)
- [End of December](roadmap-reviews/2020/review_2_december_19.md)
- [End of June](roadmap-reviews/2020/review_3_june_20.md)


These time windows will also be used to review and update all stakeholders with
the status of the in-toto implementation.
