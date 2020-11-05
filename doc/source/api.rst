API
===

The in-toto API provides various functions and :doc:`classes <model>` that you
can use to generate, consume, modify and verify in-toto metadata, as a more
feature-rich, programmable alternative to the :doc:`command line tools
<command-line-tools/index>`.


Evidence Generation
-------------------

.. autofunction:: in_toto.runlib.in_toto_run
.. autofunction:: in_toto.runlib.in_toto_record_start
.. autofunction:: in_toto.runlib.in_toto_record_stop


Supply Chain Verification
-------------------------

.. autofunction:: in_toto.verifylib.in_toto_verify

Key Utilities
-------------

in-toto uses the in-house crypto library `securesystemslib
<https://github.com/secure-systems-lab/securesystemslib>`_ to generate and
verify cryptographic signatures. Useful securesystemslib API functions, e.g. to
generate asymmetric key pairs and import them into a format that aligns with
the `in-toto metadata specification
<https://github.com/in-toto/docs/blob/v0.9/in-toto-spec.md#4-document-formats>`_,
are documented below.

Generate Key Pairs
^^^^^^^^^^^^^^^^^^
.. autofunction:: securesystemslib.interface.generate_and_write_rsa_keypair
.. autofunction:: securesystemslib.interface.generate_and_write_rsa_keypair_with_prompt
.. autofunction:: securesystemslib.interface.generate_and_write_unencrypted_rsa_keypair
.. autofunction:: securesystemslib.interface.generate_and_write_ed25519_keypair
.. autofunction:: securesystemslib.interface.generate_and_write_ed25519_keypair_with_prompt
.. autofunction:: securesystemslib.interface.generate_and_write_unencrypted_ed25519_keypair

Load Signing Keys
^^^^^^^^^^^^^^^^^
.. autofunction:: securesystemslib.interface.import_privatekey_from_file
.. autofunction:: securesystemslib.interface.import_rsa_privatekey_from_file
.. autofunction:: securesystemslib.interface.import_ed25519_privatekey_from_file

Load Verification Keys
^^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: securesystemslib.interface.import_publickeys_from_file
.. autofunction:: securesystemslib.interface.import_ed25519_publickey_from_file
.. autofunction:: securesystemslib.interface.import_rsa_publickey_from_file
.. autofunction:: securesystemslib.gpg.functions.export_pubkey
.. autofunction:: securesystemslib.gpg.functions.export_pubkeys
