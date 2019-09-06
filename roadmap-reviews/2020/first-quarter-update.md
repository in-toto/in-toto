# First quarter milestone ROADMAP update

We're past the first quarter of our [roadmap for 2020](https://github.com/in-toto/in-toto/blob/develop/ROADMAP.md
) and it is time to do a review of how the in-toto reference implementation is
holding up to it's goals for this year. In this document, we will cover the
activities from May 2019 to August 2019 in the context of the goals for this
ROADMAP as well as other newsworthy developments.

## documentation
Preparing and formalizing the Documentation is underway. For now, we have just
added the boilerplate code for the existing documentation, and we will slowly
include docs for the major in-toto modules. We expect to ramp up the activities
in this front now that other goals have been fulfilled.

In addition to the Sphinx documentation, we also reviewed our metadata compiler
(i.e., a toolchain to prepare in-toto metadata so it can be inlined on docs)
and greatly simplified it. This will be very handy for metadata examples
throughout the documentation.

Finally, we reviewed our existing README's and worked to improve their clarity
and usefulness. Thanks to everybody in the community for the feedback on this!

### Relevant issues:
* [sphinx boilerplate](https://github.com/in-toto/in-toto/pull/298)
* [in-toto metdata compiler and examples](https://github.com/in-toto/docs/pull/5)
* [better documentation overview](https://github.com/in-toto/docs/blob/master/README.md)


## CII Silver badge

We worked greatly to achieve our silver badge during this first quarter. This
required us to do a thorough review of our processes, as well as tightening
parts of it so we met the criteria. To provide a better tracking, we created
the ["CII Silver" (silver
colored)](https://github.com/in-toto/in-toto/issues?utf8=%E2%9C%93&q=label%3A%22CII+silver%22+)
on our issues. You can also see the results of the silver badge self-review
[here](https://bestpractices.coreinfrastructure.org/en/projects/1523)


## Working towards 1.0

We started this year gearing up for 1.0 and, although there's plenty to do, we
are starting to see the fruits of our work. A bump on a major release requires
work on many fronts, icluding a standard API specification, a standard CLI
specification, documentation and Spec + ITE compliance, among other issues.

In order to track the progress towards 1.0, we created a milestone, and
reviewed all the existing tickets and added some that were missing.  Here's a
quick rundown on how we did this quarter:

- Created new and assigned existing issues: 15 open:
    - API Specification, 5 open issues
    - CLI Specification, 5 open issues
    - ITE and Spec compliance: 4 open issues and 2 closed
    - Documentation: 2 closed issues
- 2 closed issues

If you want more granular information and are willing to help in-toto reach [1.0 take a look at the tickets under our milestone](https://github.com/in-toto/in-toto/issues?q=is%3Aopen+is%3Aissue+milestone%3A%22in-toto+1.0%22)

## new release 0.4.0

We are preparing this quarter's release. This includes:

- Fully spec compliant artifact rule processing.
- Add new features to the OpenPGP implementation.
- Improved testing, static analysis and packaging for downstreams.

Version 0.4.0 is being prepared in [here](https://github.com/in-toto/in-toto/pull/300)


## Hello CNCF!

During this quarter we were accepted into the CNCF as a Sandbox Project. This
means that we will get more visibility in the cloud-native space. As part of
this project, the CNCF SIG-Security group did a thorough security assesment,
that helped us further tighten our release process and identify opportunity
areas to become an overall better security product.

## New Logo!

As part of this, and to celebrate our inclusion into the CNCF, we have an
updated logo. You can take a look at it the CNCF website [here](https://github.com/cncf/artwork/blob/master/examples/sandbox.md#in-toto-logos)


## Closing remarks

This quarter was filled with exciting news and progress for the in-toto
project. We are very excited to increase industry collaboration to improve the
security of the software supply chain. We are making strides towards the goals
described on this year's ROADMAP.
