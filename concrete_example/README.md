# Concrete example

This folder contains a "concrete example" that showcases many different elements
of the toto metadata specification. This includes Delegations, Link requirements
and link metadata.

## Scenario description

In order to showcase this metadata, we assume a scenario like this:

0.- We have three stages of development of a new variant of the linux kernel
1.- The upstream repository will tag a release (they reached 1.0!), and their
sources will be used by a third-party buildbot, to create the binaries. This
buildbot is trusted, yet outside of the project owner's jurisdiction, and thus
the project owner doesn't know which steps will be taken to compile this new
kernel (could it be two stages? three?). Due to this, the buildbot phase is
delegated to a key that was agreed by both parties beforehand.
2.- These binaries are shipped to the packager, who will bundle everything and
ensure everything falls into the right path. Once packaging is done, a new
linux.tar.gz release file is sent to the client!A

## How to use these scripts 

You can run main.py, subchain.py and links.py on this folder. The first two will
output the layout to stdout, and they can easily be piped into a file:

```bash
./main.py > root.layout
```

The last one will populate a [stepname].link file for each step on the current
directory.
