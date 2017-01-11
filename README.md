# in-toto
in-toto is a series of scripts to protect the supply chain integrity.

# About in-toto
in-toto guarantees that the end-user (or owner) is able to verify that the entire development life cycle has been conducted as per the specified layout and that each of the functionaries (participants) have perfomed the specified tasks and there haven't been any malicious changes in the files.

in-toto requires a project layout that specifies the functionaries and the tasks they are supposed to perform.
After each functionary performs its task, a link metadata is generated.
This metadata is used to verify the intermediate and final products with the project layout.

# in-toto demo
You can try in-toto by running the demo application at [https://github.com/in-toto/in-toto/tree/develop/demo].
The demo basically outlines three users viz., Alice (project owner), Bob (functionary) and Carl (functionary) and how in-toto helps to specifiy a project layout and verify that the layout has been followed in a correct manner.

- Alice speficies the layout with Bob and Carl's public keys and signs it with her private key.
- Bob writes a python script and in-toto hashes the product and stores it to a piece of link metadata. The metadata is signed with Bob's private key. Bob sends the python script to Carl for packaging.
- Carl packages the script into a tarball and in-toto stores the hash to the metadata.
- The client (end-user) can now verify the final product which contains the layout, tarball, the both link metadata. The in-toto-verify command basically checks whether the layout hasn't expried and if the steps were performed according to the layout definitions.

# Using in-toto
* Clone our [repository](https://github.com/in-toto/in-toto.git).
* Run setup.py
* Start using the in-toto run and verify scripts

# Contributing to in-toto
To contribute to in-toto, follow the below mentioned steps:-
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

Submit a Pull Request and start contributing to in-toto.

# Specifications
You can read more about how in-totoworks by taking a look at our [specification](https://github.com/toto-framework/toto-framework.github.io/raw/master/toto-spec.pdf).