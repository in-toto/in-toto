# in-toto
Protecting the software supply chain integrity

in-toto guarantees that the end-user (or client) is able to verify that the entire development life cycle has been conducted as per the specified layout and that each of the functionaries (eg. developers) have performed the specified tasks and there haven't been any malicious changes in the files.

in-toto requires a project layout that specifies the functionaries and the tasks they are supposed to perform.
After each functionary performs his or her task a link metadata is generated.
This metadata is used to verify the intermediate and final products with the project layout.


## Getting Started

### Install Dependencies
 - [Python](www.python.org) in version 2.7 - crypto libraries require header files
 - [OpenSSL](https://www.openssl.org/) - crypto libraries require header files
 - [git](https://git-scm.com/) - version control system
 - [pip](https://pip.pypa.io) - package installer tool
 - [virtualenvs](http://docs.python-guide.org/en/latest/dev/virtualenvs/) - optional but strongly recommended

### Installation
```shell
# Fetch in-toto sources
git clone https://github.com/in-toto/in-toto.git

# Change into project root directory
cd in-toto

# Install with pip in "develop mode"
pip install -e .
```
### Create layout, run supply chain steps and verify final product

#### Layout

The in-toto software supply chain layout consists of the following parts:
 - **expiration date**
 - **functionary keys** (public keys, used to verify link metadata signatures)
 - **signatures** (one or more layout signatures created with the project owner key(s))
 - **software supply chain steps** correspond to steps carried out by a functionary as part of the software supply chain. The steps defined in the layout list the functionaries who are authorized to carry out the step (by key id). Steps require a unique name to associate them (upon verification) with link metadata that is created when a functionary carries out the step using the `in-toto` tools.
Additionally, steps must have material and product rules which define the files a step is supposed to operate on. Material and product rules are described in the section below.
 - **inspections** define commands to be run during the verification process and can also list material and product rules.

*Hint: Take a look at [`create_layout.py`](https://github.com/in-toto/in-toto/blob/develop/demo/owner_alice/create_layout.py), a script that creates the in-toto demo layout.*

#### Artifact Rules
A software supply chain usually operates on a set of files, such as source code, executables, packages, or the like. in-toto calls these files artifacts or more precisely materials and products.
A material describes the state of an artifact before a step or inspection has been carried out and a product describes its state thereafter.

The in-toto layout provides a simple rule language to authorize or enforce the artifacts that should be used as materials for or result from the execution of a step or inspection and to link subsequent steps and inspections together. This adds the following guarantees for any given step or inspection:
- Only artifacts **authorized** by the project owner are created, modified or deleted,
- each defined creation, modification or deletion is **enforced**, and also
- restricted to the scope of its definition, which **links** subsequent steps and inspections together.

Note that it is up to you to provide the desired security guarantees, by authorizing, enforcing and linking material and product together using any and usually multiple of the following rules:
- `CREATE <pattern>`
- `DELETE <pattern>`
- `MODIFY <pattern>`
- `ALLOW <pattern>`
- `REQUIRE <pattern>`
- `DISALLOW <pattern>`
- `MATCH <pattern> [IN <source-path-prefix>] WITH (MATERIALS|PRODUCTS) [IN <destination-path-prefix>] FROM <step>`

*Rule arguments specified as `<pattern>` allow for Unix shell-style wildcards as implemented by Python's [`fnmatch`](https://docs.python.org/2/library/fnmatch.html).*

To learn more about the different rule types, their guarantees and how they are applied take a look at the [Artifact Rules](https://docs.google.com/document/d/1TpcMIMEKWvgRHYmFZ7OtM_iNrhmUaMUoot3XO29uhuo/edit#heading=h.fv3n0caa9km) section of the in-toto sepcification.

#### Carrying out software supply chain steps

##### in-toto-run
`in-toto-run` executes the passed command and records the path and hash of the passed *materials* - files before command execution - and *products* - files after command execution and optionally stores them together with the *byproducts* of the command - return value, stdout, stderr - to a link file (`<step-name>.link`), signed with the functionary's key.

```shell
in-toto-run  --step-name <unique step name>
             --key <functionary private key path>
            [--materials <filepath>[ <filepath> ...]]
            [--products <filepath>[ <filepath> ...]]
            [--record-byproducts]
            [--verbose] -- <cmd> [args]
```


##### in-toto-record
`in-toto-record` works similar to `in-toto-run` but can be used for multi-part software supply chain steps, i.e. steps that are not carried out by a single command. Use `in-toto-record ... start ...` to create a preliminary link file that only records the *materials*, then run the commands of that step, and finally use `in-toto-record ... stop ...` to record the *products* and generate the actual link metadata file.

```shell
in-toto-record  --step-name <unique step name>
                --key <functionary private key path>
               [--verbose]
Commands:
               start [--materials <filepath>[ <filepath> ...]]
               stop  [--products <filepath>[ <filepath> ...]]
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
               --layout-keys (<layout pubkey path>,...)
```

## in-toto demo
You can try in-toto by running the [demo application](https://github.com/in-toto/in-toto/tree/develop/demo).
The demo basically outlines three users viz., Alice (project owner), Bob (functionary) and Carl (functionary) and how in-toto helps to specify a project layout and verify that the layout has been followed in a correct manner.

## Specification
You can read more about how in-toto works by taking a look at the [specification](https://github.com/toto-framework/toto-framework.github.io/raw/master/toto-spec.pdf).