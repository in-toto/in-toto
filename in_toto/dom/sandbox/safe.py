"""
  Authors: Phil Hassey, Armon Dadgar, Moshe Kaplan

  Start Date: March 2007

  Description:

  There are 3 main components to this code:
    Code safety analysis
      This is done by creating an AST for the code, walking 
      through it node by node, and checking that only safe nodes
      are used and that no unsafe strings are present.

    Executing safe code
      This is done by creating a dictionary with a key for each built-in
      function, and then running the code using that dictionary as our
      'context'.
     
    SafeDict Class
      This is a dict that prevents 'unsafe' values from being added.
      SafeDict is used by virtual_namespace (for the safe eval) as the
      dictionary of variables that will be accessible to the running code. The
      reason it is important to prevent unsafe keys is because it is possible
      to use them to break out of the sandbox. For example, it is possible to
      change an objects private variables by manually bypassing python's name
      mangling.

  The original version of this file was written by Phil Hassey. it has since
  been heavily rewritten for use in the Seattle project.

  Comments:

  Licensing:
    This file is public domain.

  Authors Comments:
    Known limitations:
    - Safe doesn't have any testing for timeouts/DoS.  One-liners
        like these will lock up the system: "while 1: pass", "234234**234234"
        This is handled by a seperate portion of Repy which manages the CPU
        usage.
    - Lots of (likely) safe builtins and safe AST Nodes are not allowed.
        I suppose you can add them to the whitelist if you want them.  I
        trimmed it down as much as I thought I could get away with and still
        have useful python code.
    - Might not work with future versions of python - this is made with
        python 2.4 in mind.  _STR_NOT_BEGIN might have to be extended
        in the future with more magic variable prefixes.  Or you can
        switch to conservative mode, but then even variables like "my_var" 
        won't work, which is sort of a nuisance.
    - If you get data back from a safe_exec, don't call any functions
        or methods - they might not be safe with __builtin__ restored
        to its normal state.  Work with them again via an additional safe_exec.
    - The "context" sent to the functions is not tested at all.  If you 
        pass in a dangerous function {'myfile':file} the code will be able
        to call it.

"""

# Reference materials:

# Built-in Objects
# http://docs.python.org/lib/builtin.html

# AST Nodes - compiler
# http://docs.python.org/lib/module-compiler.ast.html

# Types and members - inspection
# http://docs.python.org/lib/inspect-types.html
# The standard type heirarchy
# http://docs.python.org/ref/types.html

# Based loosely on - Restricted "safe" eval - by Babar K. Zafar
# (it isn't very safe, but it got me started)
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/496746

# Securing Python: Controlling the abilities of the interpreter
# (or - why even trying this is likely to end in tears)
# http://us.pycon.org/common/talkdata/PyCon2007/062/PyCon_2007.pdf

import os           # This is for some path manipulation
import sys          # This is to get sys.executable to launch the external process
import time         # This is to sleep

try:
  import compiler     # Required for the code safety check
except ImportError:
  import ast as compiler

try:
  from UserDict import DictMixin    # This is to get DictMixin
  import UserDict
  class MyMixin(UserDict.DictMixin):
    pass
except ImportError:
  from collections import MutableMapping as DictMixin
  from collections import UserDict
  class MyMixin(UserDict, DictMixin):
    pass
import platform     # This is for detecting Nokia tablets
import threading    # This is to get a lock
import subprocess   # This is to start the external process
try:
  import __builtin__ as builtins
except ImportError:
  import builtins

import six

import in_toto.dom.util.harshexit as harshexit  # This is to kill the external process on timeout
import in_toto.dom.exceptions as exception_hierarchy # For exception classes

# Fix to make repy compatible with Python 2.7.2 on Ubuntu 11.10,
# see SeattleTestbed/repy_v2#24.
subprocess.getattr = getattr

# SafeDict needs hasattr for `update`, see SeattleTestbed/repy_v2#125
UserDict.hasattr = hasattr

# Armon: This is how long we will wait for the external process
# to validate the safety of the user code before we timeout, 
# and exit with an exception
# Increased from 10 to 15 seconds per SeattleTestbed/repy_v1#90.
EVALUTATION_TIMEOUT = 15

if platform.machine().startswith('armv'):
  # The Nokia needs more time to evaluate code safety, especially
  # when under heavy loads
  EVALUTATION_TIMEOUT = 200

"""
Repyv2 Changes

NODE_ATTR_OK:
  Allow '__' in strings.
    Added: 'value'


_NODE_CLASS_OK:
  Allow exceptions
    Added: 'TryExcept', 'TryFinally', 'Raise', 'ExcepthandlerType', 'Invert',
   
_BUILTIN_OK:    
  Disallow exiting directly, use exitall instead.
    Removed: 'exit', 'quit
  
  Needed for tracebackrepy
    Added: 'isinstance', 'BaseException', 'WindowsError', 'type', 'issubclass'
    
  Allow primitive marshalling to be built
    Added: 'ord', 'chr'
    
  Repy V2 doesn't allow print()
    Removed: 'Print', 'Printnl'

_STR_OK:
  Added:
    '__repr__', '__str__'
    
"""

# This portion of the code is for the Code safety analysis
# This is done by creating an AST for the code, walking 
# through it node by node, and checking that only safe nodes
# are used and that no unsafe strings are present.

_STR_OK = ['__init__','__del__','__iter__', '__repr__', '__str__']

# __ is not allowed because it can be used to access a 'private' object in a class
# by bypassing Python's name mangling.
_STR_NOT_CONTAIN = ['__']
_STR_NOT_BEGIN = ['im_','func_','tb_','f_','co_',]

# Disallow these exact strings.
# encode and decode are not allowed because of the potential for
# encoding bugs, see SeattleTestbed/repy_v1#120.
_STR_NOT_ALLOWED = ['encode','decode'] 

def _is_string_safe(token):
  """
  <Purpose>
    Checks if a string is safe based on rules defined in
    _STR_OK, _STR_NOT_CONTAIN, and _STR_NOT_BEGIN
    

  <Arguments>
    token: A value to check.

  <Returns>
    True if token is safe, false otherwise
  """

  # If it's not a string, return True
  if type(token) is not str and type(token) is not str:
    return True
  
  # If the string is explicitly allowed, return True
  if token in _STR_OK:
    return True
    
  # Check if the string is specifically prohibited:
  if token in _STR_NOT_ALLOWED:
    return False

  # Check all the prohibited sub-strings
  for forbidden_substring in _STR_NOT_CONTAIN:
    if forbidden_substring in token:
      return False

  # Check all the prohibited prefixes
  # Return True if it is safe.
  return not token.startswith(tuple(_STR_NOT_BEGIN))


_NODE_CLASS_OK = [
    'Add', 'And', 'AssAttr', 'AssList', 'AssName', 'AssTuple',
    'Assert', 'Assign','AugAssign', 'Bitand', 'Bitor', 'Bitxor', 'Break',
    'CallFunc', 'Class', 'Compare', 'Const', 'Continue',
    'Dict', 'Discard', 'Div', 'Ellipsis', 'Expression', 'FloorDiv',
    'For', 'Function', 'Getattr', 'If', 'Keyword',
    'LeftShift', 'List', 'ListComp', 'ListCompFor', 'ListCompIf', 'Mod',
    'Module', 'Mul', 'Name', 'Node', 'Not', 'Or', 'Pass', 'Power',
    'Return', 'RightShift', 'Slice', 'Sliceobj',
    'Stmt', 'Sub', 'Subscript', 'Tuple', 'UnaryAdd', 'UnarySub', 'While',
    # New additions
    'TryExcept', 'TryFinally', 'Raise', 'ExcepthandlerType', 'Invert',

    # Python 3 additions
    'Expr', 'Call', 'Load', 'Index', 'Str', 'Store', 'Attribute', "Num",
    ]

if os.environ.get("REPY_ALLOW_UNSAFE_PRINT"):
  # XXX: print statements in python 3 are not any of these nodes, so be careufl
  _NODE_CLASS_OK.extend(['Printnl', 'Print'])


_NODE_ATTR_OK = ['value']


def _check_node(node):
  """
  <Purpose>
    Examines a node, its attributes, and all of its children (recursively) for
    safety. A node is safe if it is in _NODE_CLASS_OK and an attribute is safe
    if it is not a unicode string and either in _NODE_ATTR_OK or is safe as is 
    defined by _is_string_safe()
  
  <Arguments>
    node: A node in an AST
    
  <Exceptions>
    CheckNodeException if an unsafe node is used
    CheckStrException if an attribute has an unsafe string 
  
  <Return>
    None
  """

  if node.__class__.__name__ not in _NODE_CLASS_OK:
    raise exception_hierarchy.CheckNodeException("Unsafe call '" +
        str(node.__class__.__name__) + "' in line " + str(node.lineno))
  
  for attribute, value in node.__dict__.items():
    # Don't allow the construction of unicode literals
    # if type(value) == unicode:
    #   raise exception_hierarchy.CheckStrException("Unsafe string '" +
    #       str(value) + "' in line " + str(node.lineno) +
    #       ", node attribute '" + str(attribute) + "'")

    if attribute in _NODE_ATTR_OK: 
      continue

    # JAC: don't check doc strings for __ and the like...,
    # see SeattleTestbed/repy_v1#107.
    if attribute == 'doc' and (node.__class__.__name__ in
      ['Module', 'Function', 'Class']):
      continue

    # Check the safety of any strings
    if not _is_string_safe(value):
      raise exception_hierarchy.CheckStrException("Unsafe string '" +
          str(value) + "' in line " + str(node.lineno) +
          ", node attribute '" + str(attribute) + "'")

  if 'getChildNodes' in dir(node):
    for child in node.getChildNodes():
      _check_node(child)
  else:
    for child in compiler.iter_child_nodes(node):
      _check_node(child)



def safe_check(code):
  """
  <Purpose>
    Takes the code as input, and parses it into an AST.
    It then calls _check_node, which does a recursive safety check for every
    node.
  
  <Arguments>
    code: A string representation of python code
    
  <Exceptions>
    CheckNodeException if an unsafe node is used
    CheckStrException if an attribute has an unsafe string 
  
  <Return>
    None
  """
  parsed_ast = compiler.parse(code)
  _check_node(parsed_ast)


# End of the code safety checking implementation
# Start code safety checking wrappers


def safe_check_subprocess(code):
  """
  <Purpose>
    Runs safe_check() in a subprocess. This is done because the AST
    safe_check() uses a large amount of RAM. By running safe_check() in a
    subprocess we can guarantee that the memory will be reclaimed when the
    process ends.
  
  <Arguments>
    code: See safe_check.
    
  <Exceptions>
    As with safe_check.
  
  <Return>
    See safe_check.
  """

  # Get the path to safe_check.py by using the original start directory of python
  path_to_safe_check = os.path.join(os.path.dirname(__file__), "safe_check.py")
  
  # Start a safety check process, reading from the user code and outputing to a pipe we can read
  try:
    proc = subprocess.Popen([sys.executable, path_to_safe_check],
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          universal_newlines=True)
  
    # Write out the user code, close so the other end gets an EOF
    #(rawoutput, _) = proc.communicate(bytes(code, 'utf-8'))
    (output, _) = proc.communicate(code)
  except Exception as e:
    raise

  
  # Wait for the process to terminate
  starttime = 0 
  #output = rawoutput.decode("utf-8")

  # Check the output, None is success, else it is a failure
  if output == "None":
    return True
  
  # If there is no output, this is a fatal error condition
  elif output == "":
    raise Exception("Fatal error while evaluating code safety!")
    
  else:
    # Raise the error from the output
    raise exception_hierarchy.SafeException(output)

# Get a lock for serial_safe_check
SAFE_CHECK_LOCK = threading.Lock()

# Wraps safe_check to serialize calls
def serial_safe_check(code):
  """
  <Purpose>
    Serializes calls to safe_check_subprocess(). This is because safe_check_subprocess()
    creates a new process which may take many seconds to return. This prevents us from
    creating many new python processes.
  
  <Arguments>
    code: See safe_check.
    
  <Exceptions>
    As with safe_check.
  
  <Return>
    See safe_check.
  """

  SAFE_CHECK_LOCK.acquire()
  try:
    return safe_check_subprocess(code)
  finally:
    SAFE_CHECK_LOCK.release()

#End of static analysis portion


# This portion of the code is for the safe exec.
# The first step is to create a dictionary with a key for each built-in function
# We then replace all built-in functions with the values in that dictionary.
# We then run our code using that dictionary as our 'context'
# When we're done, we restore the original __builtin__ from a backup 


# safe replacement for the built-in function `type()`
_type = type
_compile_type = _type(compile('','','exec'))

def safe_type(*args, **kwargs):
  if len(args) != 1 or kwargs:
    raise exception_hierarchy.RunBuiltinException(
      'type() may only take exactly one non-keyword argument.')

  # Fix for SeattleTestbed/repy_v1#128, block access to Python's `type`.
#  if _type(args[0]) is _type or _type(args[0]) is _compile_type:
#    raise exception_hierarchy.RunBuiltinException(
#      'unsafe type() call.')
  # JAC: The above would be reasonable, but it is harsh.   The wrapper code for
  # the encasement library needs to have a way to check the type of things and
  # these might be inadvertantly be types.   It is hard to know if something
  # is a type
  if args[0] == safe_type or args[0] == _type or _type(args[0]) is _type:
    return safe_type

  if _type(args[0]) is _type or _type(args[0]) is _compile_type:
    raise exception_hierarchy.RunBuiltinException(
      'unsafe type() call.')

  return _type(args[0])

# This dict maps built-in functions to their replacement functions
_BUILTIN_REPLACE = {
  'type': safe_type
}

# The list of built-in exceptions can be generated by running the following:
# r = [v for v in dir(__builtin__) if v[0] != '_' and v[0] == v[0].upper()] ; r.sort() ; print r
_BUILTIN_OK = [
  '__debug__',
    
  'ArithmeticError', 'AssertionError', 'AttributeError', 'DeprecationWarning',
  'EOFError', 'Ellipsis', 'EnvironmentError', 'Exception', 'False',
  'FloatingPointError', 'FutureWarning', 'IOError', 'ImportError',
  'IndentationError', 'IndexError', 'KeyError', 'KeyboardInterrupt',
  'LookupError', 'MemoryError', 'NameError', 'None', 'NotImplemented',
  'NotImplementedError', 'OSError', 'OverflowError', 'OverflowWarning',
  'PendingDeprecationWarning', 'ReferenceError', 'RuntimeError', 'RuntimeWarning',
  'StandardError', 'StopIteration', 'SyntaxError', 'SyntaxWarning', 'SystemError',
  'SystemExit', 'TabError', 'True', 'TypeError', 'UnboundLocalError',
  'UnicodeDecodeError', 'UnicodeEncodeError', 'UnicodeError',
  'UnicodeTranslateError', 'UserWarning', 'ValueError', 'Warning', 'ZeroDivisionError',
    
  'abs', 'bool', 'cmp', 'complex', 'dict', 'divmod', 'filter', 'float', 
  'frozenset', 'hex', 'id', 'int', 'len', 'list', 'long', 'map', 'max', 'min',
  'object', 'oct', 'pow', 'range', 'reduce', 'repr', 'round', 'set', 'slice',
  'str', 'sum', 'tuple',  'xrange', 'zip','id',
    
  #Added for repyv2
  'isinstance', 'BaseException', 'WindowsError', 'type', 'issubclass',
  'ord', 'chr', 
 
  # added for py3 support
  'print', 'exec', 'Attribute', 'split'
  
  # debugging goodies :) 
  '__import__', 'hasattr', 'getattr', 'any',  '__build_class__', 
  ]

    
_BUILTIN_STR = ['copyright','credits','license','__name__','__doc__',]


def _replace_unsafe_builtin(unsafe_call):
  # This function will replace any unsafe built-in function
  def exceptionraiser(*vargs,**kargs):
    raise exception_hierarchy.RunBuiltinException("Unsafe call '{}'".format(unsafe_call))# + 
#        str(unsafe_call) + "' with args '" + str(vargs) + "', kwargs '" + 
#        str(kargs) + "'")
  return exceptionraiser


# Stores the current list of allowed built-in functions.
_builtin_globals = None

# Stores a backup copy of all the built-in functions
_builtin_globals_backup = None


# Populates `_builtin_globals` with keys for every built-in function
# The values will either be the actual function (if safe), a replacement 
# function, or a stub function that raises an exception.
def _builtin_init():
  global _builtin_globals, _builtin_globals_backup
  
  # If _builtin_init() was already called there's nothing to do
  if _builtin_globals != None:
    return
  
  # Create a backup of the built-in functions
  #TODO: Perhaps pull this out of the function -  Is there a reason to do this more then once?
  _builtin_globals_backup = builtins.__dict__.copy()
  _builtin_globals = {}

  for builtin in builtins.__dict__.keys():
    # It's important to check _BUILTIN_REPLACE before _BUILTIN_OK because
    # even if the name is defined in both, there must be a security reason
    # why it was supposed to be replaced, and not just allowed.
    if builtin in _BUILTIN_REPLACE:
      replacewith = _BUILTIN_REPLACE[builtin]
    elif builtin in _BUILTIN_OK: 
     replacewith = builtins.__dict__[builtin]
    elif builtin in _BUILTIN_STR:
      replacewith = ''
    else:
      # Replace the function with our exception-raising variant
      replacewith = _replace_unsafe_builtin(builtin)
    _builtin_globals[builtin] = replacewith

  # Armon: Make SafeDict available
  _builtin_globals["SafeDict"] = get_SafeDict

  # Make the repy exception hierarchy available
  # This is done by making every exception in _EXPORTED_EXCEPTIONS
  # available as a built-in
  for exception_name in exception_hierarchy._EXPORTED_EXCEPTIONS:
    _builtin_globals[exception_name] = exception_hierarchy.__dict__[exception_name]

# Replace every function in __builtin__ with the one from _builtin_globals.
def _builtin_destroy():
  _builtin_init()
  for builtin_name, builtin in _builtin_globals.items():
    builtins.__dict__[builtin_name] = builtin

# Restore every function in __builtin__ with the backup from _builtin_globals_backup.
def _builtin_restore():
  for builtin_name, builtin in _builtin_globals_backup.items():
    builtins.__dict__[builtin_name] = builtin

# Have the builtins already been destroyed?
BUILTINS_DESTROYED = False


def safe_run(code,context=None):
  """
  <Purpose>
    Executes code with only safe builtins.
    If context is passed in, those keys will be available to the code.
  
  <Arguments>
    code: A string representation of python code
    context: A dictionary of variables to execute 'in'
    
  <Exceptions>
    exception_hierarchy.RunBuiltinException if an unsafe call is made
    Whatever else the source code may raise
  
  <Return>
    None
  """
  global BUILTINS_DESTROYED
 
  if context == None:
    context = {}
  
  # Destroy the builtins if needed
  if not BUILTINS_DESTROYED:
    BUILTINS_DESTROYED = True
    _builtin_destroy()
   
  try:
    context['__builtins__'] = _builtin_globals
    exec(code, context)
  finally:
    _builtin_restore()


# Convenience functions

def safe_exec(code, context = None):
  """
  <Purpose>
    Checks the code for safety. It then executes code with only safe builtins.
    This is a wrapper for calling serial_safe_check() and safe_run()
  
  <Arguments>
    code: A string representation of python code
    context: A dictionary of variables to execute 'in'
    
  <Exceptions>
    CheckNodeException if an unsafe node is used
    CheckStrException if an attribute has an unsafe string
    exception_hierarchy.RunBuiltinException if an unsafe call is made
    Whatever else the code may raise
  
  <Return>
    None
  """
  serial_safe_check(code)
  safe_run(code, context)


# This portion of the code defines a SafeDict
# A SafeDict prevents keys which are 'unsafe' strings from being added.


# Functional constructor for SafeDict to allow us to safely map it into the
# repy context.
def get_SafeDict(*args,**kwargs):
  return SafeDict(*args,**kwargs)


#class SafeDict(UserDict, DictMixin):
class SafeDict(MyMixin):
  """
  <Purpose>
    A dictionary implementation which prohibits "unsafe" keys from being set or
    get. This is done by checking the key with _is_string_safe().
    
    SafeDict is used by virtual_namespace (for the safe eval) as the dictionary
    of variables that will be accessible to the running code. The reason it is
    important to prevent unsafe keys is because it is possible to use them to
    break out of the sandbox. For example, it is possible to change an object's
    private variables by manually bypassing python's name mangling.
  """

  def __init__(self,from_dict=None):
    # Create the underlying dictionary
    self.__under__ = {}

    # Break if we are done...
    if from_dict is None:
      return
    if type(from_dict) is not dict and not isinstance(from_dict,SafeDict):
      return

    # If we are given a dict, try to copy its keys
    for key,value in from_dict.items():
      # Skip __builtins__ and __doc__ since safe_run/python inserts that
      if key in ["__builtins__","__doc__"]:
        continue

      # Check the key type
      if type(key) is not str and type(key) is not str:
        raise TypeError("'SafeDict' keys must be of string type!")

      # Check if the key is safe
      if _is_string_safe(key):
        self.__under__[key] = value

      # Throw an exception if the key is unsafe
      else:
        raise ValueError("Unsafe key: '"+key+"'")

  # Allow getting items
  def __getitem__(self,key):
    if type(key) is not str and type(key) is not str:
      raise TypeError("'SafeDict' keys must be of string type!")
    if not _is_string_safe(key):
      raise ValueError("Unsafe key: '"+key+"'")

    return self.__under__.__getitem__(key)

  # Allow setting items
  def __setitem__(self,key,value):
    if type(key) is not str and type(key) is not str:
      raise TypeError("'SafeDict' keys must be of string type!")
    if not _is_string_safe(key):
      raise ValueError("Unsafe key: '"+key+"'")

    return self.__under__.__setitem__(key,value)

  # Allow deleting items
  def __delitem__(self,key):
    if type(key) is not str and type(key) is not str:
      raise TypeError("'SafeDict' keys must be of string type!")
    if not _is_string_safe(key):
      raise ValueError("Unsafe key: '"+key+"'")

    return self.__under__.__delitem__(key)

  # Allow checking if a key is set
  def __contains__(self,key):
    if type(key) is not str and type(key) is not str:
      raise TypeError("'SafeDict' keys must be of string type!")
    if not _is_string_safe(key):
      raise ValueError("Unsafe key: '"+key+"'")

    return key in self.__under__

  # Return the key set
  def keys(self):

    # Filter out the unsafe keys from the underlying dict
    safe_keys = []

    for key in self.__under__.keys():
      if _is_string_safe(key):
        safe_keys.append(key)

    # Return the safe keys
    return safe_keys

  # Allow us to be printed.
  # Overriding __repr__ gets around an infinite loop issue,
  # SeattleTestbed/repy_v1#111, for simple cases.
  # It seems unlikely this is adequate for more complex cases (like safedicts
  # that refer to each other)
  def __repr__(self):
    #return "ayylmao"
    newdict = {}
    for safekey in list(self.keys()):
      if self.__under__[safekey] == self:
        newdict[safekey] = newdict
      else:
        newdict[safekey] = self.__under__[safekey]
    return newdict.__repr__()


  # Allow a copy of us
  def copy(self):
    # Create a new instance
    copy_inst = SafeDict(self.__under__)

    # Fix for recursion depth reached when copying and printing a
    # SafeDict containing a reference to itself.
    # https://github.com/SeattleTestbed/repy_v2/issues/97
    # Caveat: dict.copy is expected to return a shallow copy, this fix
    # introduces a partial deep copy for the contained self reference
    for key, value in self.__under__.items():
      if value is self:
        copy_inst[key] = copy_inst

    # Return the new instance
    return copy_inst

  # Make our fields read-only
  # This means __getattr__ can do its normal thing, but any
  # setters need to be overridden to prohibit adding/deleting/updating

  def __setattr__(self,name,value):
    # Allow setting __under__ on initialization
    if name == "__under__" and name not in self.__dict__:
      self.__dict__[name] = value
      return
    raise TypeError("'SafeDict' attributes are read-only! ({}, {})".format(name, value))

  def __delattr__(self,name):
    raise TypeError("'SafeDict' attributes are read-only!")
