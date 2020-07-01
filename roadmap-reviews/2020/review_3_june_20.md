# ROADMAP review (End of June '20)

We have reached the end of our 2020 roadmap and it is time to do a final review
of how the in-toto reference implementation has held up to its goals for this
year. In this document, we will cover the activities from January to June 2020
in the context of the goals for this ROADMAP as well as other newsworthy
developments.


## Documentation and stable API

Our main objective of the past year was to revise and consolidate all of the
in-toto code- and usage-documentation in order to tie down the public API for
a 1.0 release.

We are very excited to announce that we did indeed finalize both the CLI
documentation that was already in the works during our last roadmap evaluation,
and have since then also created comprehensive API and metadata
model documentation, and updated and added many usage examples.

This work includes among other things a revision and standardization of the
docstrings of all public-facing functions, classes and methods, as well as
their automated release on [in-toto.readthedocs.io](https://in-toto.readthedocs.io).

### Relevant documents

- Automate documentation
  ([#276](https://github.com/in-toto/in-toto/issues/276))
- Revise and consolidate documentation
  ([#284](https://github.com/in-toto/in-toto/issues/284))
- Major CLI documentation overhaul and automation
  ([#341](https://github.com/in-toto/in-toto/pull/341))
- Revise and update source code documentation and build with sphinx
  ([#369](https://github.com/in-toto/in-toto/pull/369))


## Working towards 1.0

Despite the vast improvements in our documentation and the resulting
stability of the API, we decided to hold off the 1.0 release until we have
sorted out one final issue. That is, a clean-up of the utility and keys module:

- Factor out in_toto.util to securesystemslib + general revision
  ([#80](https://github.com/in-toto/in-toto/issues/80))

Some of below issues will be closed together with
[#80](https://github.com/in-toto/in-toto/issues/80), others will be carried
over into the next roadmap, and some were deemed to no longer qualify for the
reference implementation roadmap at all.

### Relevant documents

- Define stable API ([#277](https://github.com/in-toto/in-toto/issues/277)) --
  *mostly addressed via [#369](https://github.com/in-toto/in-toto/pull/369)
  modulo [#80](https://github.com/in-toto/in-toto/issues/80), will be addressed
  early on as part of roadmap '21*
- Revisit exception taxonomy
  ([#126](https://github.com/in-toto/in-toto/issues/126)) -- *the current
  taxonomy is now thoroughly documented via
  [#369](https://github.com/in-toto/in-toto/pull/369) but the issue is kept to
  motivate future enhancements as part of the roadmap '21*
- Verify in-toto's supply chain with in-toto
  ([#278](https://github.com/in-toto/in-toto/issues/278)) -- *will be carried
  over to the roadmap '21*
- Parametrize writing of inspection links
  ([#260](https://github.com/in-toto/in-toto/issues/260)) -- *no more roadmap
  priority, also see [#364](https://github.com/in-toto/in-toto/pull/364) for
  important preparatory work for the issue*
- Require fully conformant metadata when loading
  ([#186](https://github.com/in-toto/in-toto/issues/186)) -- *no more roadmap
  priority*
- Integrate/require inspection commands
  ([#109](https://github.com/in-toto/in-toto/issues/109)) -- *no more roadmap
  priority*
- Revisit artifact rule path patterns
  ([#32](https://github.com/in-toto/docs/issues/32)) -- *was transferred to
  specification issue tracker*


We are working hard to make 1.0 become a reality early in the next roadmap.



## Preparing 0.5.0

We are preparing this evaluation period's pre-release, which includes a bug
fix, a new feature and clean-up work in the unit test suite.

### Relevant documents

- Bugfix: Use kwargs in in-toto-run to fix lstrip-paths bug
  ([#340](https://github.com/in-toto/in-toto/pull/340))
- Feature: Add a flag to accept a target directory to put generated metadata
  ([#364](https://github.com/in-toto/in-toto/pull/364))
- Tests: Add tmp dir and gpg key test mixins
  ([#345](https://github.com/in-toto/in-toto/pull/345))
- Tests: Use constant from securesystemslib to detect GPG in tests
  ([#352](https://github.com/in-toto/in-toto/pull/352))
- Tests: Enhance test suite feedback on Windows
  ([#368](https://github.com/in-toto/in-toto/pull/368))

## Tangential work
On a related side-note, together with the TUF team we have made exciting
progress in in-toto's in-house crypto and utility library -- *securesystemslib*:

### Relevant documents

- A PKCS11-based HSM interface
  ([#229](https://github.com/secure-systems-lab/securesystemslib/pull/229))
- nistp384 signature verification support
  ([#228](https://github.com/secure-systems-lab/securesystemslib/pull/228))
- A filesystem abstraction for non-local filesystems
  ([#232](https://github.com/secure-systems-lab/securesystemslib/pull/232))

We plan to adopt some of these features for in-toto in next as part of roadmap
'21.


### Closing remarks.

We acknowledge that we missed our main roadmap '20 goal, that is the release of
in-toto 1.0. But it should be noted that it is a close miss and we are
confident about our decision to hold off the release until we have dealt with
the last remaining blemish (i.e.
[#80](https://github.com/in-toto/docs/issues/80), so that we can guarantee the
longer-term stability of the 1.0 API.

What is more, we are proud of the many enhancements and the strengthening the
reference implementation received in the past year and continues to receive.
With the help of many talented students and an ever-growing open source
community, the in-toto reference implementation will certainly maintain and
also expand its central role in the supply chain security ecosystem, both as a
production-ready tool, and also as a reference for other the many emerging
in-toto implementations.
