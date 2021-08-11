Roadmap
=======

_Note: Previous roadmaps can be found with the roadmap reviews for that period.
[Link to Roadmap 2020](roadmap-reviews/2020/ROADMAP.md)_

This document spans the Roadmap for the in-toto main implementation for the
time window from August 2020 to August 2021. The main focus of this year is to
achieve spec compliance and agreement between all the different implementers,
integrators and users throughout the in-toto ecosystem. 

## The 1.0 milestone

Although the previous years's roadmap aimed to culminate with in-toto's 1.0
release, we decided to hold off for a couple of months before we committed to
such an important milestone. The main rationale is that there are some
outstanding tickets we have not been able to squash. We'd much rather tag
in-toto 1.0 once those are fixed.

## New ITE compliance

There has been quite the activity in the in-toto specification world. Namely,
there are three new ITE's related to integration with existing technologies and
tracking abstract artifacts. This year we will focus on making sure the
reference implementation can provide for these community-sought-for plans.

Since the first two ITEs relate to TUF integration, we will make sure we have a
tighter testing harness with co-dependent libraries (e.g., securesystemslib).
In addition we will make sure common elements (such as public key components
and signatures) can be cross-verifiable by both implementations.

A broader ITE is ITE-4, which focuses on abstract resources. This is paramount
for some uses, such as the CNAB security specification. In this case, we will
be adding facilities for custom artifact hashers/resolvers. We also envision
providing some baseline catalog of these hashers for common usecases so that
people have something to reference when writing their own and --- of course ---
use them.

## CII Gold badge

in-toto is already marked as "Silver" under the Core Infrastructure Initiative
best practices badge. This year we aim to upgrade our rating to "Gold". To work
towards this goal, we'll review and comply with the few missing requirements
for the gold badge.

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
- [End of July](roadmap-reviews/2021/review_3_july_21.md)

These time windows will also be used to review and update all stakeholders with
the status of the in-toto implementation.
