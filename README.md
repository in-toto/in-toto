# in-toto [![Build Status](https://travis-ci.org/in-toto/in-toto.svg?branch=develop)](https://travis-ci.org/in-toto/in-toto) [![Coverage Status](https://coveralls.io/repos/github/in-toto/in-toto/badge.svg?branch=develop)](https://coveralls.io/github/in-toto/in-toto?branch=develop) [![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/1523/badge)](https://bestpractices.coreinfrastructure.org/projects/1523)

in-toto provides a framework to protect the integrity of the software supply chain. It does so by verifying that each task in the chain is carried out as planned, by authorized personnel only, and that the product is not tampered with in transit.

in-toto requires a **project owner** to create a **layout**. A layout lists the sequence of **steps** of the software supply chain, and the **functionaries** authorized to perform these steps.
When a functionary performs a step in-toto gathers information about the used command and the related files and stores it in a **link** metadata file. As a consequence link files provide the required evidence to establish a continuous chain that can be validated against the steps defined in the layout.

The layout, signed by the project owners, together with the links, signed by the designated functionaries, are released as part of the final product, and can be validated manually or via automated tooling in, e.g. a package manager.


## Getting Started

### Install Dependencies
 - [Python](www.python.org) in version 2.7 - crypto libraries require header files
 - [OpenSSL](https://www.openssl.org/) - crypto libraries require header files
 - [git](https://git-scm.com/) - version control system
 - [pip](https://pip.pypa.io) - package installer tool

### Installation
It is strongly recommended to install in-toto in an isolated Python environment. For easy setup instructions visit the docs for [`virtualenv`](https://virtualenv.pypa.io) and the convenient [`vitualenvwrapper`](https://virtualenvwrapper.readthedocs.io).

```shell
pip install in-toto
```
### Create layout, run supply chain steps and verify final product

#### Layout

The in-toto software supply chain layout consists of the following parts:
 - **expiration date**
 - **readme** (an optional description of the supply chain)
 - **functionary keys** (public keys, used to verify link metadata signatures)
 - **signatures** (one or more layout signatures created with the project owner key(s))
 - **software supply chain steps**
   correspond to steps carried out by a functionary as part of the software supply chain. The steps defined in the layout list the functionaries who are authorized to carry out the step (by key id). Steps require a unique name to associate them (upon verification) with link metadata that is created when a functionary carries out the step using the `in-toto` tools. Additionally, steps must have material and product rules which define the files a step is supposed to operate on. Material and product rules are described in the section below.
 - **inspections** define commands to be run during the verification process and can also list material and product rules.

Take a look at the [demo layout creation example](layout-creation.md)
for further information on how to create an in-toto layout. Or try our
experimental [layout creation web tool](https://in-toto.engineering.nyu.edu/).



#### Artifact Rules
A software supply chain usually operates on a set of files, such as source code, executables, packages, or the like. in-toto calls these files artifacts. A material is an artifact that will be used when a step or inspection is carried out. Likewise, a product is an artifact that results from carrying out a step.

The in-toto layout provides a simple rule language to authorize or enforce the artifacts of a step and to chain them together. This adds the following guarantees for any given step or inspection:
- Only artifacts **authorized** by the project owner are created, modified or deleted,
- each defined creation, modification or deletion is **enforced**, and also
- restricted to the scope of its definition, which **chains** subsequent steps and inspections together.

Note that it is up to you to properly secure your supply chain, by authorizing, enforcing and chaining materials and products using any and usually multiple of the following rules:
- `CREATE <pattern>`
- `DELETE <pattern>`
- `MODIFY <pattern>`
- `ALLOW <pattern>`
- `DISALLOW <pattern>`
- `MATCH <pattern> [IN <source-path-prefix>] WITH (MATERIALS|PRODUCTS) [IN <destination-path-prefix>] FROM <step>`

*Rule arguments specified as `<pattern>` allow for Unix shell-style wildcards as implemented by Python's [`fnmatch`](https://docs.python.org/2/library/fnmatch.html).*

To learn more about the different rule types, their guarantees and how they are applied take a look at the [Artifact Rules](https://github.com/in-toto/docs/blob/master/in-toto-spec.md#433-artifact-rules) section of the in-toto specification.

#### Carrying out software supply chain steps

##### in-toto-run
`in-toto-run` executes the passed command and records the path and hash of
the passed *materials* - files before command execution - and *products* -
files after command execution and optionally stores them together with the
command's *byproducts* (e.g: return value, stdout or stderr) to a link file
(`<NAME>.<KEYID-PREFIX>.link`), signed with the functionary's key.

```shell
in-toto-run  --step-name <unique step name>
            {--key <functionary signing key path>,  --gpg [<functionary gpg signing key id>]}
            [--gpg-home <path to gpg keyring>]
            [--materials <filepath>[ <filepath> ...]]
            [--products <filepath>[ <filepath> ...]]
            [--record-streams]
            [--no-command]
            [--verbose] -- <cmd> [args]
```


##### in-toto-record
`in-toto-record` works similar to `in-toto-run` but can be used for
multi-part software supply chain steps, i.e. steps that are not carried out
by a single command. Use `in-toto-record start ...` to create a
preliminary link file that only records the *materials*, then run the
commands of that step or edit files manually and finally use
`in-toto-record stop ...` to record the *products* and generate the actual
link metadata file.

```shell
usage: in-toto-record start --step-name <unique step name>
                            (--key <signing key path> | --gpg [<gpg keyid>])
                            [--gpg-home <gpg keyring path>] [-v]
                            [--materials <material path> [<material path> ...]]

usage: in-toto-record stop -step-name <unique step name>
                           (--key <signing key path> | --gpg [<gpg keyid>])
                           [--gpg-home <gpg keyring path>] [-v]
                           [--products <product path> [<product path> ...]]
```

#### Release final product

In order to verify the final product with in-toto, the verifier must have access to the layout, the `*.link` files,
and the project owner's public key(s).

#### Verification
Use `in-toto-verify` on the final product to verify that
- the layout was signed with the project owner's private key(s),
- has not expired,
- each step was performed and signed by the authorized functionary,
- the functionaries used the commands, they were supposed to use,
- materials and products of each step were in place as defined by the rules, and
- run the defined inspections

```shell
in-toto-verify --layout <layout path>
               {--layout-keys <filepath>[ <filepath> ...],  --gpg <keyid> [ <keyid> ...]}
               [--gpg-home <path to gpg keyring>]
               [--verbose]
```


#### Settings
Settings can be configured in [`in_toto.settings`](https://github.com/in-toto/in-toto/blob/develop/in_toto/settings.py), via prefixed environment variables or in RCfiles in one of the following
paths: */etc/in_toto/config, /etc/in_totorc, \~/.config/in_toto/config,
\~/.config/in_toto, \~/.in_toto/config, \~/.in_totorc, .in_totorc*.

A setting in an RCfile in the current working directory overrides
the same
setting in an RCfile in the user's home directory, which overrides the
same setting in an environment variable, which overrides the same setting
in `in_toto.settings`.

Setting names are restricted to the below listed settings (case sensitive).
Also, setting values that contain colons are parsed as list.

##### Available Settings

`ARTIFACT_EXCLUDE_PATTERNS` Specifies a list of glob patterns that can be used to
exclude files from being recorded as materials or products. See [runlib
docs for more details](https://github.com/in-toto/in-toto/blob/develop/in_toto/runlib.py#L93-L114).

`ARTIFACT_BASE_PATH` If set, material and product paths passed to
`in-toto-run` are searched relative to the set base path. Also, the base
path is stripped from the paths written to the resulting link metadata
file.

##### Examples
```shell
# Bash style environment variable export
export IN_TOTO_ARTIFACT_BASE_PATH='/home/user/project'
export IN_TOTO_ARTIFACT_EXCLUDE_PATTERNS='*.link:.gitignore'
```
```
# E.g in rcfile ~/.in_totorc
[in-toto settings]
ARTIFACT_BASE_PATH=/home/user/project
ARTIFACT_EXCLUDE_PATTERNS=*.link:.gitignore

```

## in-toto demo
You can try in-toto by running the [demo application](https://github.com/in-toto/demo).
The demo basically outlines three users viz., Alice (project owner), Bob (functionary) and Carl (functionary) and how in-toto helps to specify a project layout and verify that the layout has been followed in a correct manner.

## Specification
You can read more about how in-toto works by taking a look at the [specification](https://github.com/in-toto/docs/raw/master/in-toto-spec.pdf).


## Security Issues and Bugs
Security issues can be reported by emailing justincappos@gmail.com.

At a minimum, the report must contain the following:
* Description of the vulnerability.
* Steps to reproduce the issue.

Optionally, reports that are emailed can be encrypted with PGP. You should use
PGP key fingerprint E9C0 59EC 0D32 64FA B35F 94AD 465B F9F6 F8EB 475A.

Please do not use the GitHub issue tracker to submit vulnerability reports. The
issue tracker is intended for bug reports and to make feature requests.

## Instructions for Contributors
Note: Development of in-toto occurs on the "develop" branch of this repository.

Contributions can be made by submitting GitHub pull requests. Take a look at
our [development
guidelines](https://github.com/secure-systems-lab/lab-guidelines/blob/master/dev-workflow.md)
for detailed instructions. Submitted code should follow our [code style
guidelines](https://github.com/secure-systems-lab/code-style-guidelines),
which provide examples of what to do (or not to do) when writing Python code.


## Acknowledgments
This project is managed by Prof. Justin Cappos and other members of the
[Secure Systems Lab](https://ssl.engineering.nyu.edu/) at NYU and the
[NJIT Cybersecurity Research Center](https://centers.njit.edu/cybersecurity).

This research was supported by the Defense Advanced Research Projects Agency
(DARPA) and the Air Force Research Laboratory (AFRL). Any opinions, findings,
and conclusions or recommendations expressed in this material are those of the
authors and do not necessarily reflect the views of DARPA and AFRL. The United
States Government is authorized to reproduce and distribute reprints
notwithstanding any copyright notice herein.
