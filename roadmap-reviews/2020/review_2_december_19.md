# ROADMAP review (End of December '19)

We're past the second evaluation period of our [roadmap for
2020](https://github.com/in-toto/in-toto/blob/develop/ROADMAP.md) and it is
time to do a review of how the in-toto reference implementation is
holding up to its goals for this year. In this document, we will cover the
activities from August 2019 to December 2019 in the context of the goals for
this ROADMAP as well as other newsworthy developments.

## Documentation

* We created the first batch of documentation, including a detailed
  installation guide and work in progress documents about all the
  command-line-client tools

During the last review we spent some time gearing up to improve the state of
our documentation. This period was mostly focusing on making this a reality. We
are happy to announce that the in-toto project documentation is now hosted on
[readthedocs](https://in-toto.readthedocs.io/en/latest/). Many things are
improving in this front, so check often for new guides, cli tool documentation,
usage examples and more!

As an added win to our improved documentation, we had the chance to simplify
and create a more succinct README. If you find things are missing there, do
check our readthedocs site!

Again, thanks to everybody in the community for the feedback on this!

### Relevant documents:
* [sphinx boilerplate](https://github.com/in-toto/in-toto/pull/298)
* [better documentation overview](https://github.com/in-toto/docs/blob/master/README.md)
* [CLI docs](https://github.com/in-toto/in-toto/pull/332)
* [Update installation instructions](https://github.com/in-toto/in-toto/pull/331)


## CII silver badge and beyond!

We achieved our silver badge, and we're almost 50% into the Gold badge now.
This is of course a hint of what we may include in our ROADMAP for next year.
You can see the results of the silver badge self-review on
[bestpractices.coreinfrastructure.org](https://bestpractices.coreinfrastructure.org/en/projects/1523).


## Working towards 1.0

We worked towards 1.0, and we are convinced we're going to make the deadline now
that we picked many issues.

Here's a quick rundown on how we did this evaluation period:

- Milestone issues: 12 open, +2 closed
  - API Specification: 5 open
  - CLI Specification: 3 open
  - ITE and Spec compliance: 4 open, +1 closed
  - Documentation: 3 open, +1 closed
- Other issues: 20 open, +3 closed


Although this delta might seem minimal, the CLI specification issues are all
holding on us quickly consolidating and documenting the CLI interface.

If you want more granular information, or if you are interested in helping in-toto reach 1.0, [take a look at the tickets under our milestone](https://github.com/in-toto/in-toto/issues?q=is%3Aopen+is%3Aissue+milestone%3A%22in-toto+1.0%22).

## New release 0.4.2

In this period we made two patch releases, which include the following changes:

- Full migration of our custom gpg subpackage and subprocess module to
  securesystemslib.
  This allows a larger community to benefit from our work, and thus broader
  support. A race condition that caused in-toto tests to fail sporadically was
  already fixed in securesystemslib and is now also available to in-toto.
- Improved documentation
- Added --version option to the CLI tools. Thanks, @MinchinWeb!
- Addressed linter warnings and tested against updated dependencies
- Improved Debian packaging

As usual, there are packages ready on [PyPI](https://pypi.org/project/in-toto/), [Arch Linux](https://www.archlinux.org/packages/community/any/in-toto/), and newly in [Debian](https://tracker.debian.org/pkg/in-toto) too.

## Closing remarks.

This winter evaluation period is shorter than our initial one. The reason
behind this is that we've focused more on working closely with industry
partners, so as to improve the stability of the tool and to help them match our
use cases. In addition, we've helped improve the state of our dependencies as we
upstream part of our codebase. This way, we are creating a better ecosystem not
only for in-toto, but for our sister project TUF.

During this period, we are confident in saying we've been making slow-but-steady
progress to fit our goals.
