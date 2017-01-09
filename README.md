# in-toto
in-toto is a series of scripts to protect the supply chain integrity.

# About in-toto
A software supply chain is the series of steps performed when writing, testing, packaging, and distributing software. A typical software supply chain is composed of multiple steps "chained" together that transform (e.g., compilation) or verify the state (e.g., linting) of the project in order to drive it to a final product.

In simple words, in-toto guarantees that the end-user (or owner) is able to verify that the entire development life cycle has been conducted as per the specified layout and that each of the functionaries (participants) have perfomed the specified tasks and there hasn't been any malicious changes in the files.

So what in-toto basically does is that it asks for a project layout (JSON) stating the layout's expiry, functionary keys and steps involved. The project owner is tasked with layout specification. The layout also specifies the functionaries and the tasks they are supposed to perform.
After each functionary performs its task, a link metadata is generated.
This metadata forms a part of the final product where it is used by the client to verify that there hasn't been any changes in the files between different steps.s

# in-toto demo
You can try in-toto by running the demo application at [https://github.com/in-toto/in-toto/tree/develop/demo].
The demo basically outlines three users viz., Alice (project owner), Bob (functionary) and Carl (functionary) and how in-toto helps to specifiy a project layout and verify that the layout has been followed in a correct manner.

- Alice speficies the layout in JSON format with Bob and Carl's public keys and signs it with her private key.
- Bob writes a python script and in-toto hashes the product and stores it to a piece of link metadata. The metadata is signed with Bob's private key. Bob sends the python script to Carl for packaging.
- Carl packages the script into a tarball and in-toto stores the hash to the metadata.
- The client (end-user) can now verify the final product which contains the layout, tarball, the both link metadata. The in-toto-verify command basically checks whether the layout hasn't expried and if the steps were performed according to the layout definitions.

# Using in-toto
We have an open-source implementation, which is still under heavy development.
You can clone our repository and run in-toto commands (run, verify, etc.) from command line.

# Contributing to in-toto

# Specifications
You can read more about how in-totoworks by taking a look at our [specification](https://github.com/toto-framework/toto-framework.github.io/raw/master/toto-spec.pdf).