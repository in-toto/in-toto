# in-toto demo

In this demo, we will use in-toto to secure a software supply chain with a very
simple workflow.
Alice will be the project owner - she creates and signs the software supply chain
layout with her private key - and Bob and Carl will be the project functionaries -
they carry out the steps of the software supply chain as defined in the layout.

For the sake of demonstrating in-toto, we will have you run all parts of the
software supply chain.
This is, you will perform the commands on behalf of Alice, Bob and Carl as well
as the client who verifies the final product.


### Download and setup in-toto on *NIX (Linux, OS X, ..)
```shell
# Make sure you have git, python and pip installed on your system
# and get in-toto
git clone -b develop --recursive https://github.com/in-toto/in-toto.git

# Change into project root directory
cd in-toto

# Install with pip in "develop mode"
# (we strongly recommend using Virtual Environments)
# http://docs.python-guide.org/en/latest/dev/virtualenvs/
pip install -e .

# Change into the demo directoy and you are ready to start
cd demo
```
Inside the demo directory you will find four directories: `owner_alice`,
`functionary_bob`, `functionary_carl` and `final_product`. Alice, Bob and Carl
already have RSA keys in each of their directories. This is what you see:
```shell
tree
# the tree command gives you the following output
# ├── README.md
# ├── final_product
# ├── functionary_bob
# │   ├── bob
# │   └── bob.pub
# ├── functionary_carl
# │   ├── carl
# │   └── carl.pub
# ├── owner_alice
# │   ├── alice
# │   ├── alice.pub
# │   └── create_layout.py
# └── run_demo.py
```

### Define software supply chain layout (Alice)
First, we will need to define the software supply chain layout. To simplify this
process, we provide a script that generates a simple layout for the purpose of
the demo. In this software supply chain layout, we have Alice, who is the project
owner that creates the layout, Bob, who uses `vi` to create a Python program
`foo.py`, and Carl, who uses `tar` to package up `foo.py` into a tarball which
together with the in-toto metadata composes the final product that will
eventually be installed and verified by the end user.

```shell
# Create and sign the software supply chain layout on behalf of Alice
cd owner_alice
python create_layout.py
```
The script will create a layout, add Bob's and Carl's public keys (fetched from
their directories), sign it with Alice's private key and dump it to `root.layout`.
In `root.layout`, you will find that (besides the signature and other information)
there are two steps, `write_code` and `package`, that the functionaries Bob
and Carl, identified by their public keys, are authorized to perform.

### Write code (Bob)
Now, we will take the role of the functionary Bob and perform the step
`write-code` on his behalf, that is we use in-toto to open an editor and record
metadata for what we do. Execute the following commands to change to Bob's
directory and perform the step.

```shell
cd ../functionary_bob
in-toto-run --step-name write-code --products foo.py --key bob -- vi foo.py
```

The command you just entered will open a `vi` editor, where you can write your
code (you can write whatever you want). After you save the file and close vi
(do this by entering `:x`), you will find `write-code.link` inside
Bob's directory. This is one piece of step link metadata that the client will
use for verification.

Here is what happens behind the scenes:
 1. In-toto wraps the command `vi foo.py`,
 1. hashes the product `foo.py`,
 1. stores the hash to a piece of link metadata,
 1. signs the metadata with Bob's private key and
 1. stores everything to `write-code.link`.

```shell
# Bob has to send the resulting foo.py to Carl so that he can package it
cp foo.py ../functionary_carl/
```

### Package (Carl)
Now, we will perform Carl’s `package` step.
Execute the following commands to change to Carl's directory and `tar` up Bob's
`foo.py`:

```shell
cd ../functionary_carl
in-toto-run --step-name package --materials foo.py --products foo.tar.gz --key carl -- tar zcvf foo.tar.gz foo.py
```

This will create another step link metadata file, called `package.link`.
It's time to release our software now.


### Verify final product (client)
Let's first copy all relevant files into the `final_product` that is
our software package `foo.tar.gz` and the related metadata files `root.layout`,
`write-code.link` and `package.link`:
```shell
cd ..
cp owner_alice/root.layout functionary_bob/write-code.link functionary_carl/package.link functionary_carl/foo.tar.gz final_product/
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
 2. was signed with Alice’s private key,
<br>and that according to the definitions in the layout
 3. each step was performed and signed by the authorized functionary
 4. the functionaries used the commands they were supposed to use (`vi`,
    `tar`)
 5. the recorded materials and products align with the matchrules and
 6. the inspection `untar` finds what it expects.


From it, you will see the meaningful output `PASSING` and a return value
of `0`, that indicates verification worked out well:
```shell
echo $?
# should output 0
```

### Tampering with the software supply chain
Now, let’s try to tamper with the software supply chain.
Imagine that someone got a hold of `foo.py` before it was passed over to
Carl (e.g., someone hacked into the version control system). We will simulate
this by changing `foo.py` on Bob's machine (in `functionary_bob` directory)
and then let Carl package and ship the malicious code.
```shell
cd ../functionary_bob
echo "something evil" >> foo.py
cp foo.py ../functionary_carl/
```
Let's switch to Carl's machine and let him run the package step which
unwittingly packages the tampered version of foo.py
```shell
cd ../functionary_carl
in-toto-run --step-name package --materials foo.py --products foo.tar.gz --key carl -- tar zcvf foo.tar.gz foo.py
```
and then again ship everything out as final product to the client:
```shell
cd ..
cp owner_alice/root.layout functionary_bob/write-code.link functionary_carl/package.link functionary_carl/foo.tar.gz final_product/
```

### Verifying the malicious product

```shell
cd final_product
in-toto-verify --layout root.layout --layout-key alice.pub
```
This time, in-toto will detect that the product `foo.py` from Bob's `write-code`
step was not used as material in Carl's `package` step (the verified hashes
won't match) and therefore will fail verification an return a non-zero value:
```shell
echo $?
# should output 1
```


### Wrapping up
Congratulations! You have completed the in-toto demo! This exercise shows a very
simple case in how in-toto can protect the different steps within the software
supply chain. More complex software supply chains that contain more steps can be
created in a similar way. You can read more about what in-toto protects against
and how to use it on [in-toto's Github page](https://in-toto.github.io/).

### Tired of copy-pasting commands?
We provide a `run_demo.py` script that sequentially executes all commands
listed above. Just change into the `demo` directory, run it and observe the
output.

```shell
# Being in in-toto root
cd demo
python run_demo.py
```
