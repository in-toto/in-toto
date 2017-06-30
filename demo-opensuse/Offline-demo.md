# in-toto offline openSUSE demo
You can try this demo if you don't have or don't want to create an OpenSUSE build service account.

# Change into the demo directory and you are ready to start
```shell
cd demo-opensuse/
```

Inside the demo-opensuse directory you will find four directories: `owner_alice`,
`functionary_bob`, `functionary_carl` and `final_product`. Alice, Bob and Carl
already have RSA keys in each of their directories. This is what you see:
```shell
tree
# the tree command gives you the following output
# ├── Dockerfile
# ├── Offline-demo.md
# ├── README.md
# ├── final_product
# ├── functionary_bob
# │   ├── bob
# │   └── bob.pub
# ├── functionary_carl
# │   ├── carl
# │   └── carl.pub
# └── owner_alice
#     ├── alice
#     ├── alice.pub
#     ├── create_layout.py
#     ├── create_layout_offline.py
#     └── verify-signature.sh
```

### Define software supply chain layout (Alice)
We will define the software supply chain layout. To simplify this process, we provide a script that generates a simple layout for the purpose of the demo.

Like in the on-line example, Alice, Bob and Carl will carry out the steps in this software supply chain. Alice is the project owner that creates the root layout. Bob, is the developer who clones the project's repo and performs some pre-packaging edits. Carl then builds the sources and verifies that its fit to ship. Carl then packages the built binary into an RPM.

Create and sign the software supply chain layout on behalf of Alice
```shell
cd owner_alice/
python create_layout_offline.py
```
The script will create a layout, add Bob's and Carl's public keys (fetched from
their directories), sign it with Alice's private key and dump it to `root.layout`.
In `root.layout`, you will find that (besides the signature and other information)
there are three steps, `clone`, `update-changelog` and `package`, that the
functionaries Bob and Carl, identified by their public keys,
are authorized to perform.

### Clone project source code (Bob)
Now, we will take the role of the functionary Bob and perform the step
`clone` on his behalf, that is we use in-toto to clone the project repo and
record metadata for what we do.
```shell
cd ../functionary_bob
in-toto-record --step-name clone --key bob start
git clone file:///home/connman/.git/
in-toto-record --step-name clone --key bob stop --products connman/_service connman/connman-1.30.tar.gz connman/connman-1.30.tar.sign connman/connman-rpmlintrc connman/connman.changes connman/connman.keyring connman/connman.spec
```

Here is what happens behind the scenes:
 1. In-toto wraps the work of Bob,
 1. hashes the contents of the source code,
 1. adds the hash together with other information to a metadata file,
 1. signs the metadata with Bob's private key, and
 1. stores everything to `clone.[Bob's keyid].link`.

### Update-changelog (Bob)
Before Carl tests and packages the source code, Bob will update the changelog saved in `connman.changes`. He does this using the `in-toto-record` command, which produces the same link metadata file as above but does not require Bob to wrap his action in a single command. So first Bob records the state of the files he will modify:
```shell
in-toto-record --step-name update-changelog --key bob start --materials connman/connman.changes
```

Then Bob uses an editor of his choice to update the changelog e.g.:
```shell
vim connman/connman.changes
```

And finally he records the state of files after the modification and produces
a link metadata file called `update-changelog.[Bob's keyid].link`.
```shell
in-toto-record --step-name update-changelog --key bob stop --products connman/connman.changes
```

Bob has done his work and can send over the sources to Carl.
```shell
mv connman update-changelog.0c6c50a1.link clone.0c6c50a1.link ../functionary_carl/
```

### Package (Carl)
Now, we will perform Carl’s `package` step by executing the following commands to change to Carl's directory.
```shell
cd ../functionary_carl/
in-toto-record --step-name package --key carl start --materials connman/*
```

Build the rpm package.
```shell
cp connman/* /usr/src/packages/SOURCES/
rpmbuild -bs connman/connman.spec
```

Get the build RPM
```shell
cp /usr/src/packages/SRPMS/connman-1.30-0.src.rpm ./connman-1.30-1.1.src.rpm
```

And finally he records the state of files after the modification and produces
a link metadata file, called `package.[Carl's keyid].link`.
```shell
in-toto-record --step-name package --key carl stop --products connman-1.30-1.1.src.rpm
```

### Verify final product (client)
Let's first copy all relevant files into the `final_product` that is
our software package `<srcpackage.rpm>` and the related metadata files `root.layout`,
`clone.[Bob's keyid].link`, `update-changelog.[Bob's keyid].link` and `package.[Carl's keyid].link`:
```shell
cd ../
cp owner_alice/root.layout owner_alice/verify-signature.sh functionary_carl/clone.0c6c50a1.link functionary_carl/update-changelog.0c6c50a1.link functionary_carl/package.c1ae1e51.link functionary_carl/connman-1.30-1.1.src.rpm final_product/
```
And now run verification on behalf of the client:
```shell
cd final_product
# Fetch Alice's public key from a trusted source to verify the layout signature
# Note: The functionary public keys are fetched from the layout
cp ../owner_alice/alice.pub .
in-toto-verify --layout root.layout --layout-key alice.pub
```

This command will verify that
 1. the layout has not expired,
 2. was signed with Alice’s private key, and that according to the definitions in the layout
 3. each step was performed and signed by the authorized functionary
 4. the recorded materials and products align with the matchrules and
 5. the inspection `unpack` finds what it expects.
 6. the inspection `verify-signature` checks that the signature for connman tarball is correct.

From it, you will see the meaningful output `PASSING` and a return value
of `0`, that indicates verification was successful:
```shell
echo $?
# should output 0
```

### Wrapping up
Congratulations! You have completed the in-toto opensuse demo!

This exercise shows a very simple case in how in-toto can protect the different steps within the software supply chain. More complex software supply chains that contain more steps can be created in a similar way. You can read more about what in-toto protects against and how to use it on [in-toto's Github page](https://in-toto.github.io/).

