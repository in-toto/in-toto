# in-toto openSUSE demo
In this demo, we will use in-toto to secure a software supply chain for OpenSUSE. Bob is a developer for a project, Carl tests the software before packaging, and Alice oversees the project. So, using in-toto's names for the parties, Alice is the project owner - she creates and signs the software supply chain layout with her private key - and Bob and Carl are project functionaries - they carry out the steps of the software supply chain as defined in the layout.

For the sake of demonstrating in-toto, we will have you run all parts of the software supply chain. That is, you will perform the commands on behalf of Alice, Bob and Carl as well as the client who verifies the final product.

# Setup
Install docker
https://docs.docker.com/engine/installation/

Get in-toto
```
git clone https://github.com/in-toto/in-toto.git
```

Build Docker image from Dockerfile
```
cd in-toto/demo-opensuse/
docker pull opensuse
docker build -t="in-toto-demo-opensuse" .
```
Run the docker image
```
docker run --privileged -i -t in-toto-demo-opensuse
```

# Change into the demo directoy and you are ready to start
```
cd home/in-toto/
source in-toto/bin/activate/
cd demo-opensuse/
```

Inside the demo-opensuse directory you will find four directories: `owner_alice`,
`functionary_bob`, `functionary_carl` and `final_product`. Alice, Bob and Carl
already have RSA keys in each of their directories. This is what you see:
```
tree  # If you don't have tree, try 'find .' instead
# the tree command gives you the following output
# ├── README.md
# ├── Dockerfile
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
#     └── create_layout.py
```

### Define software supply chain layout (Alice)
First, we will create a new package on open build server and we will need to define the software supply chain layout. To simplify this process, we provide a script that generates a simple layout for the purpose of the demo.

In this software supply chain layout, we have Alice, who is the project owner that creates the layout, Bob, who clones the project's repo and performs some pre-packaging editing (update changelog), Carl, then tests the build and verifies that its fit to ship, Carl then commits the package which triggers open build server to build the RPMs.

First, signup for an account on opensuse build service at
https://build.opensuse.org/ICSLogin/

Export your username as environment variable so that you can copy paste the demo commands
```
username=<username>
```

Checkout your default project. You will be prompted for your username and password which is stored in `~/.oscrc` as plain text.
```
cd owner_alice/
osc checkout home:$username
```

Specify the build target
```
osc meta prj -e home:$username
```

This will open a template xml in your favourite editor. For this demo uncomment the first one.
```
<repository name="openSUSE_Factory">
   <path project="openSUSE:Factory" repository="standard" />
   <arch>x86_64</arch>
   <arch>i586</arch>
 </repository>
```

Create a new package named connman in your home project
```
cd home:$username
osc meta pkg -e home:$username connman
```

osc will open a template xml, fill out name, title, description.
You can see your package here https://build.opensuse.org/package/show/home:$username/connman. Remember replace $username with your actual username.

Update the local copy from the central server. you will get a new connman directory
```
osc up
```

Create and sign the software supply chain layout on behalf of Alice
```
cd ..
python create_layout.py
```
The script will create a layout, add Bob's and Carl's public keys (fetched from
their directories), sign it with Alice's private key and dump it to `root.layout`.
In `root.layout`, you will find that (besides the signature and other information)
there are four steps, `clone`, `update-changelog`, `test` and `package`, that
the functionaries Bob and Carl, identified by their public keys, are authorized
to perform.

### Clone project source code (Bob)
Now, we will take the role of the functionary Bob and perform the step
`clone` on his behalf, that is we use in-toto to clone the project repo from GitHub and
record metadata for what we do. Execute the following commands to change to Bob's
directory and perform the step.

```
cd ../functionary_bob
mv ../owner_alice/home:$username/ ./
in-toto-record --step-name update-changelog --key bob start
git clone https://github.com/shikherverma/connman.git
mv connman/* home:$username/connman/
rm -r connman/
in-toto-record --step-name clone --key bob stop --products home:$username/connman/_service home:$username/connman/connman-1.30.tar.gz home:$username/connman/connman-1.30.tar.sign home:$username/connman/connman-rpmlintrc home:$username/connman/connman.changes home:$username/connman/connman.keyring home:$username/connman/connman.spec
```

Here is what happens behind the scenes:
 1. In-toto wraps the work of Bob,
 1. hashes the contents of the source code,
 1. adds the hash together with other information to a metadata file,
 1. signs the metadata with Bob's private key, and
 1. stores everything to `clone.[Bob's keyid].link`.

### Update-changelog (Bob)
Before Carl tests and commits the source code, Bob will update the changelog saved in `connman.changes`. He does this using the `in-toto-record` command, which produces the same link metadata file as above but does not require Bob to wrap his action in a single command. So first Bob records the state of the files he will modify:
```
in-toto-record --step-name update-changelog --key bob start --materials home:$username/connman/connman.changes
```

Then Bob uses an editor of his choice to update the changelog e.g.:
```
vim home:$username/connman/connman.changes
```

And finally he records the state of files after the modification and produces
a link metadata file called `update-changelog.[Bob's keyid].link`.
```
in-toto-record --step-name update-changelog --key bob stop --products home:$username/connman/connman.changes
```

Bob has done his work and can send over the sources to Carl.
```
mv home:$username/ ../functionary_carl/
```

### Test (Carl)
Now, we will perform Carl’s `test` step by executing the following commands to change to Carl's directory.

```
cd ../functionary_carl/
cd home:$username
in-toto-run --step-name test --key ../carl -- osc build openSUSE_Factory x86_64 connman/connman.spec
mv test.c1ae1e51.link ..
cd ..
```
This will create a step link metadata file, called `test.[Carl's keyid].link`.

### Package (Carl)
Now we will execute the package step.
```
in-toto-record --step-name package --key carl start --materials home:$username/connman/*
```

Commit changes, this would trigger an automatic build on open build server.
```
cd home:$username/connman
osc add *
osc commit
```

Download the build RPM from server
```
cd ../../
wget http://download.opensuse.org/repositories/home:/shikher/openSUSE_Factory/src/connman-1.30-1.1.src.rpm
```

And finally he records the state of files after the modification and produces
a link metadata file, called `package.[Carl's keyid].link`.
```
in-toto-record --step-name package --key carl stop --products connman-1.30-1.1.src.rpm
```

### Verify final product (client)
Let's first copy all relevant files into the `final_product` that is
our software package `<srcpackage.rpm>` and the related metadata files `root.layout`,
`clone.[Bob's keyid].link`, `update-changelog.[Bob's keyid].link`, `test.[Carl's keyid].link` and `package.[Carl's keyid].link`:
```
cd ..
cp owner_alice/root.layout functionary_bob/clone.0c6c50a1.link functionary_bob/update-changelog.0c6c50a1.link functionary_carl/test.c1ae1e51.link functionary_carl/package.c1ae1e51.link functionary_carl/connman-1.30-1.1.src.rpm final_product/
```
And now run verification on behalf of the client:
```
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

From it, you will see the meaningful output `PASSING` and a return value
of `0`, that indicates verification worked out well:
```
echo $?
# should output 0
```

### Clean up
We will delete the connman package from your home project now.
```
cd ../functionary_carl/home:$username
osc delete connman
osc ci -m "remove package"
```

### Wrapping up
Congratulations! You have completed the in-toto opensuse demo! This exercise shows a very simple case in how in-toto can protect the different steps within the software supply chain. More complex software supply chains that contain more steps can be created in a similar way. You can read more about what in-toto protects against and how to use it on [in-toto's Github page](https://in-toto.github.io/).

