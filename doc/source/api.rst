API
===

The in-toto API provides various functions and :doc:`classes <model>` that you can use
to generate, consume, modify and verify in-toto metadata, as a more
feature-rich, programmable alternative to the :doc:`command line tools <command-line-tools/index>`.


Evidence Generation
-------------------

.. autofunction:: in_toto.runlib.in_toto_run
.. autofunction:: in_toto.runlib.in_toto_record_start
.. autofunction:: in_toto.runlib.in_toto_record_stop


Supply Chain Verification
-------------------------

.. autofunction:: in_toto.verifylib.in_toto_verify

Utilities
---------

.. todo::

  Document `in-toto.util` in accordance with `#80 <https://github.com/in-toto/in-toto/issues/80>`_
