in-toto-run
===========

in-toto run is the main wrapper for in-toto to generate link metadata while
carrying out a step. To do this, it wraps any command passed, and attempts to
track all relevant information about the wrapped command's execution.


Basic Usage
-----------

in-toto-run has two required arguments. First, a step name, which can be passed
as follows:


--name (or -n) <name>:
  the step name. This is used to populate the "name" field in the link metadata
  as well as picking up the name of the link metadata file (i.e.,
  name.xxxx.link).

Then, one key parameter. You can pass a key parameter with one of the following
options:

--key (or -k) <keyfile>:
  Use a private key contained in the keyfile parameter. This key can be one of
  rsa or ed25519 keys, created with :doc:`in-toto-keygen` or a PKCSv5 or 8 PEM
  generated with your tool of choice (e.g., openssl).

--gpg (or -g) [keyid]:
  Use your gpg key to sign instead. If you omit the keyid parameter, the
  default key in your default keyring will be used instead.

If you want in-toto-run to track the materials and products as they are
generated use the --materials and --products flags (or -m and -p).

.. code-block:: sh

    # track all materials on the current directory 
    # (recursively) and then products from the 
    # build subdirectory
    in-toto-run -k mykey -n myname -m . -p build 


Usage Examples
--------------

Generating a piece of link metadata with no materials, but products (e.g., when
generating files using no input):

.. code-block:: sh

    # track no materials, but I created foo.c, so 
    # mark that as a product
    in-toto-run -k mykey -n myname -p foo.c -- touch foo.c


Using in-toto-run to generate a link that doesn't require a command to be run:

.. code-block:: sh

    # Use in-toto to generate a signed attestation for 
    # a pdf document I manually reviewed. I'll mark the 
    # pdf as a material to my manual review process
    in-toto-run -k mykey -n myname -m document.pdf -x 


