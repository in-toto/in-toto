# in-toto
in-toto is a series of scripts to protect the supply chain integrity.

# About in-toto
in-toto guarantees that the end-user (or client) is able to verify that the entire development life cycle has been conducted as per the specified layout and that each of the functionaries (eg. developers) have performed the specified tasks and there haven't been any malicious changes in the files.

in-toto requires a project layout that specifies the functionaries and the tasks they are supposed to perform.
After each functionary performs its task, a link metadata is generated.
This metadata is used to verify the intermediate and final products with the project layout.

# in-toto demo
You can try in-toto by running the demo application at [demo application](https://github.com/in-toto/in-toto/tree/develop/demo).
The demo basically outlines three users viz., Alice (project owner), Bob (functionary) and Carl (functionary) and how in-toto helps to specify a project layout and verify that the layout has been followed in a correct manner.

# Getting Started
## 1. Installation

*Make sure you have git, python and pip installed on your system*
*and get in-toto*

git clone -b develop --recursive https://github.com/in-toto/in-toto.git

*Change into project root directory*

cd in-toto

*Install with pip in "develop mode"*
*(we strongly recommend using Virtual Environments)*
*http://docs.python-guide.org/en/latest/dev/virtualenvs/*

pip install -e .

*Export the envvar required for "simple settings"*

export SIMPLE_SETTINGS=in_toto.settings

*Install additional requirements that for some good reason are not in the*
*requirements file*

pip install pycrypto cryptography

## 2. Create layout

The layout should specify 6 parts:-
  1. "_type": which defines a layout
  2. "expires": which sets the expiry date of the layout
  3. "inspect": which defines the material and product match rules
  4. "keys": which specifies the public keys of the functionaries
  5. "signature": which denotes the private key of the owner
  6. "steps": which describes the steps involved and the functionaries who are authorized to perform them

You can use the create_layout.py script or write your own script to specify a layout for your project.

## 3. Perform software supply chain steps

The following commands are used while performing software supply chain:-
  1. in-toto-record:
  This command provides an interface to start and stop link metadata recording.
  It takes a step name and a functionary's signing key (along with the optional material paths),
  creates a temporary link file and signs it with the functionary's key.

  2. in-toto-run:
  This command provides an interface which takes a link command as input and wraps metadata recording.

## 4. Release final product

In order to verify the final product with in-toto, the verifier must have access to the layout, the *.link files,
and the project owner's public key.

## 5. Verify final product

  1. in-toto-verify:
  This command will verify that
    * the layout has not expired,
    * was signed with the owner's private key, 
    * and that according to the definitions in the layout
      * each step was performed and signed by the authorized functionary
      * the functionaries used the commands they were supposed to use (vi, tar)
      * the recorded materials and products align with the matchrules and
      * the inspection untar finds what it expects.

# Specifications
You can read more about how in-toto works by taking a look at our [specification](https://github.com/toto-framework/toto-framework.github.io/raw/master/toto-spec.pdf).