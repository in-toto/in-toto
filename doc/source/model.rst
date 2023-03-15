Metadata Model
==============

The in-toto metadata model classes are used internally and may be required as
arguments to or returned by in-toto :doc:`api` functions (see
:func:`in_toto.runlib.in_toto_run` and :func:`in_toto.verifylib.in_toto_verify`).

They provide containers and convenience methods to generate, sign, serialize
and read or write in-toto conformant metadata (see
:doc:`layout-creation-example`).


Metadata
-----------
.. autoclass:: in_toto.models.metadata.Metadata
  :inherited-members:
  :members:

DSSE Envelope
-------------
.. autoclass:: in_toto.models.metadata.Envelope
  :inherited-members:
  :members:

Metablock
---------
.. autoclass:: in_toto.models.metadata.Metablock
  :inherited-members:
  :members:

Link
----
.. autoclass:: in_toto.models.link.Link
  :inherited-members:
  :members:

Layout
------
.. autoclass:: in_toto.models.layout.Layout
  :inherited-members:
  :members:

Step
----
.. autoclass:: in_toto.models.layout.Step
  :inherited-members:
  :members:

Inspection
----------
.. autoclass:: in_toto.models.layout.Inspection
  :inherited-members:
  :members:
