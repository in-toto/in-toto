in-toto-sign
============

in-toto-sign lets you sign arbitrary pieces of in-toto link and layout
metadata. For links, it is useful to re-sign old metadata (e.g., when changing
keys), or to sign unsigned links generated with :doc:`in-toto-mock`. For
layouts, it is useful to append signatures in case threshold signing of layouts
is necessary.

Basic Usage
-----------

in-toto-sign requires the following two required parameters:

--key (or -k) keyfile:
    The signing private key used to sign this piece of link metadata, located
    in keyfile.

--file (or -f) filename:
    The piece of link or layout metadata to sign.

Alternatively, you can replace the key parameter with ``--gpg`` or ``-g`` to
use a gpg keyring.

in-toto-sign tries to guess an appropriate filename for the files that it signs
(e.g., if a link file is passed, the format ``name.keyidprefix.link`` is used),
but you can also use the ``-o`` parameter if you wish to use a specific output
filename.


Usage Examples
--------------

Signing a layout:

.. code-block:: sh

    # sign a layout under mylayout.layout
    in-toto-sign -k mykey -f mylayout.layout
    # a signed root.layout is created

Signing a link:

.. code-block:: sh
    
    # Sign a link under stepname.link
    in-toto-sign -k mykey -f stepname.link
    # a link, called stepname.xxxxx.link is created


Appending a signature (e.g., for threshold signing of layouts):

.. code-block:: sh

    in-toto-sign -k mykey -f root.layout -a
