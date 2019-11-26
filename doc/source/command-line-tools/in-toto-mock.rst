in-toto-mock
============

in-toto-mock is a variant of :doc:`in-toto-run` that lets you generate unsigned
link metadata. This is useful if you, for example, want to generate link
metadata, inspect it and sign if afterwards.


Basic Usage
-----------

Given that no cryptographic signing is involved, in-toto-mock only requires you
to pass a name paramter using ``--name`` or ``-n`` parameter. Other parameters
are shared from :doc:`in-toto-run` (e.g., ``-p`` for products and ``-m`` for
materials)

Usage Examples
--------------

You can use in-toto-mock to generate unsigned link metadata, inspect it, and
sign it afterwards:

.. code-block:: sh

    # generate the link
    in-toto-mock -n touch -- touch file

    # inspect the link
    vi touch.link

    # use in-toto sign to sign
    in-toto-sign -k mykey -f touch.link
    # link touch.xxxxxx.link is created hedre
