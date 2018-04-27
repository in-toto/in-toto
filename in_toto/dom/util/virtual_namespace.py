"""
<Author>
  Armon Dadgar

<Start Date>
  October 21st, 2009

<Description>
  This module provides the VirtualNamespace object. This object allows
  arbitrary code to be checked for safety, and evaluated within a
  specified global context.
"""

import in_toto.dom.sandbox.safe as safe
from in_toto.dom.exceptions import *

# This is to work around safe...
safe_compile = compile

# Functional constructor for VirtualNamespace
def createvirtualnamespace(code, name):
  return VirtualNamespace(code,name)

# This class is used to represent a namespace
class VirtualNamespace(object):
  """
  The VirtualNamespace class is used as a wrapper around an arbitrary
  code string that has been verified for safety. The namespace provides
  a method of evaluating the code with an arbitrary global context.
  """

  # Constructor
  def __init__(self, code, name):
    """
    <Purpose>
      Initializes the VirtualNamespace class.

    <Arguments>
      
      code:
          (String) The code to run in the namespace

      name:
          (String, optional) The name to use for the code. When the module is
          being executed, if there is an exception, this name will appear in
          the traceback.

    <Exceptions>
      A safety check is performed on the code, and a CodeUnsafeError exception will be raised
      if the code fails the safety check. 

      If code or name are not string types, a RepyArgumentError exception will be raised.
    """
    # Check for the code
    # Do a type check
    if type(code) is not str:
      raise RepyArgumentError("Code must be a string!")

    if type(name) is not str:
      raise RepyArgumentError("Name must be a string!" + str(type(name)))

    # Remove any windows carriage returns
    code = code.replace('\r\n','\n')

    # Do a safety check
    try:
      safe.serial_safe_check(code)
    except Exception as e:
      raise CodeUnsafeError("Code failed safety check! Error: "+str(e))

    # All good, store the compiled byte code
    self.code = safe_compile(code,name,"exec")


  # Evaluates the virtual namespace
  def evaluate(self,context):
    """
    <Purpose>
      Evaluates the wrapped code within a context.

    <Arguments>
      context: A global context to use when executing the code.
      This should be a SafeDict object, but if a dict object is provided
      it will automatically be converted to a SafeDict object.

    <Exceptions>
      Any that may be raised by the code that is being evaluated.
      A RepyArgumentError exception will be raised if the provided context is not
      a safe dictionary object or a ContextUnsafeError if the
      context is a dict but cannot be converted into a SafeDict.

    <Returns>
      The context dictionary that was used during evaluation.
      If the context was a dict object, this will be a new
      SafeDict object. If the context was a SafeDict object,
      then this will return the same context object.
    """
    # Try to convert a normal dict into a SafeDict
    if type(context) is dict:
      try:
        context = safe.SafeDict(context)
      except Exception as e:
        raise ContextUnsafeError("Provided context is not safe! Exception: "+str(e))

    # Type check
    if not isinstance(context, safe.SafeDict):
      raise RepyArgumentError("Provided context is not a safe dictionary!")

    # Call safe_run with the underlying dictionary
    safe.safe_run(self.code, context.__under__)

    # Return the dictionary we used
    return context


