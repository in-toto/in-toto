in-toto-verify
==============

in-toto-verify is the main verification tool on the suite, and it is used to
verify a delivered product against its software supply chain metadata (i.e.,
its layout and the corresponding links). 

If you are looking for a tool to verify signatures on individual
metadata/layout files, take a look at :doc:`in-toto-sign` instead.


Basic Usage
-----------

in-toto-verify only accepts to paramters: the location of the layout file and
the location of the project owner's public key. The rest of the information
(such as which links to load) is derived from the Layout.

.. code-block:: sh

    # verify this layout and links using alice's public key
    in-toto-verify -k alice.pub -l root.layout

This will use alice's public key to verify the integrity of the layout, and
then continue veriication following the policy specified in the layout itself.

Link file location
------------------

Links need be in the current directory, and they must be named
`stepname.keyidprefix.link` as defined in the specification. Both
:doc:`in-toto-run` and :doc:`in-toto-record` will generate link metadata named
like this. If you require special handling of the in-toto link metadata files,
please take a look at the library api to modify this behavior.


Sublayouts
----------

If your layout includes sublayouts, in-toto will recurse into a subdirectory
named `stepname.keyidprefix`, where all the links relevants to that sublayout
must exist. The sublayout itself will be contaiend where the link file usually
is (i.e., `stepname.keyidprefix.link`)
