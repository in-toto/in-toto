in-toto-record
==============

in-toto-record is a more versatile, powerful alternative to :doc:`in-toto-run`.
It provides a facility to "record" the state of the host before and after the
step is actually executed. This is useful if, for example, there are many steps
chained together, or the step's execution is something manual like editing a
file.

Basic Usage
-----------

Like :doc:`in-toto-run`, you will need to pass a name and a cryptographic key
parameter. In addition, you need to execute the `start` and `stop` commands to
start recording and stop recording respectively.

.. code-block:: sh

    # Start recording my steps execution
    in-toto-record start -k mykey -n myname -m src

    # perform many complex operations, up to and 
    # including compiling the code by hand
    ...

    # Finally, stop the recording:
    in-toto-record stop -k mykey -n myname -p build

in-toto-record shares many of the flags of :doc:`in-toto-run`
