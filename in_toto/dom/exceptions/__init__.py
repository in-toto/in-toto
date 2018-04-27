"""

This file contains the exception hierarchy for repy. This allows repy modules
to import a single file to have access to all the defined exceptions.

"""

# This list maintains the exceptions that are exported to the user
# If the exception is not listed here, the user cannot explicitly
# catch that error.
_EXPORTED_EXCEPTIONS = ["RepyException",
                        "RepyArgumentError",
                        "CodeUnsafeError",
                        "ContextUnsafeError",
                        "ResourceUsageError",
                        "ResourceExhaustedError",
                        "ResourceForbiddenError",
                        "LockDoubleReleaseError",
                        "TimeoutError",
                       ]



##### High-level, generic exceptions

class InternalRepyError (Exception):
  """
  All Fatal Repy Exceptions derive from this exception.
  This error should never make it to the user-code.
  """
  pass

class RepyException (Exception):
  """All Repy Exceptions derive from this exception."""
  pass

class RepyArgumentError (RepyException):
  """
  This Exception indicates that an argument was provided
  to a repy API as an in-appropriate type or value.
  """
  pass

class TimeoutError (RepyException):
  """
  This generic error indicates that a timeout has
  occurred.
  """
  pass


##### Code Safety Exceptions

class CodeUnsafeError (RepyException):
  """
  This indicates that the static code analysis failed due to
  unsafe constructions or a syntax error.
  """
  pass

class ContextUnsafeError (RepyException):
  """
  This indicates that the context provided to evaluate() was
  unsafe, and could not be converted into a SafeDict.
  """
  pass


##### Resource Related Exceptions

class ResourceUsageError (RepyException):
  """
  All Resource Usage Exceptions derive from this exception.
  """
  pass

class ResourceExhaustedError (ResourceUsageError):
  """
  This Exception indicates that a resource has been
  Exhausted, and that the operation has failed for that
  reason.
  """
  pass

class ResourceForbiddenError (ResourceUsageError):
  """
  This Exception indicates that a specified resource
  is forbidden, and cannot be used.
  """
  pass


##### Safety exceptions from safe.py

class SafeException(RepyException):
    """Base class for Safe Exceptions"""
    def __init__(self,*value):
        self.value = str(value)
    def __str__(self):
        return self.value

class CheckNodeException(SafeException):
    """AST Node class is not in the whitelist."""
    pass

class CheckStrException(SafeException):
    """A string in the AST looks insecure."""
    pass

class RunBuiltinException(SafeException):
    """During the run a non-whitelisted builtin was called."""
    pass


##### Lock related exceptions

class LockDoubleReleaseError(RepyException):
  """
  This exception indicates that an attempt was made to
  release a lock that was not acquired.
  """
  pass
