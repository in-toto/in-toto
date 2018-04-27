""" 
Author: Justin Cappos

Start Date: September 17th, 2008

Description:
Module for printing clean tracebacks.   It takes the python traceback and 
makes the output look nicer so the programmer can tell what is happening...

"""


# and don't want traceback to use linecache because linecache uses open
# Need to be able to reference the last traceback...
import sys

# We need the service logger to log internal errors -Brent
# import servicelogger

# Used to determine whether or not we use the service logger to log internal
# errors.  Defaults to false. -Brent
# WARNING: Changing this to True manually may break tracebackrepy
servicelog = False

# this is the directory where the node manager resides.   We will use this
# when deciding where to write our service log.
logdirectory = None

import in_toto.dom.util.harshexit as harshexit
import in_toto.dom.exceptions as exception_hierarchy
import os 

# This list contains all the modules which are black-listed from the
# traceback, so that if there is an exception, they will not appear in the
# "user" (filtered) traceback.
TB_SKIP_MODULES = ["repy.py", "safe.py", "virtual_namespace.py", 
    "namespace.py", "emulcomm.py", "emultimer.py", "emulmisc.py", 
    "emulfile.py", "nonportable.py", "socket.py"]



# sets the user's file name.
# also sets whether or not the servicelogger is used. -Brent
def initialize(useservlog=False, logdir = '.'):
  global servicelog
  global logdirectory

  if useservlog:
    import servicelogger

  servicelog = useservlog
  logdirectory = logdir


def format_exception():
  """
  <Purpose>
    Creates a string containing traceback and debugging information
    for the current exception that is being handled in this thread.

  <Side Effects>
    Calls sys.exc_clear(), so that we know this current exception has been
    "handled".

    NOTE WELL:
      Ensure that this function does not raise excpetions itself (even 
      if it handles them). This will override the original exception 
      we are trying to handle, and `sys.exc_info` / `sys.exc_clear` will 
      not do the right thing. For reference, see the Python 2 docs:
      https://docs.python.org/2.7/library/sys.html#sys.exc_info

  <Returns>
    A human readable string containing debugging information. Returns
    None if there is no exception being handled.

  This is an example traceback:
  ---
  Following is a full traceback, and a user traceback.
  The user traceback excludes non-user modules. The most recent call is displayed last.

  Full debugging traceback:
    "repy.py", line 191, in main
    "/Users/adadgar/Projects/seattle/trunk/test/virtual_namespace.py", line 116, in evaluate
    "/Users/adadgar/Projects/seattle/trunk/test/safe.py", line 304, in safe_run
    "dylink.repy", line 472, in <module>
    "dylink.repy", line 360, in dylink_dispatch
    "dylink.repy", line 455, in evaluate
    "/Users/adadgar/Projects/seattle/trunk/test/namespace.py", line 1072, in __do_func_call
    "/Users/adadgar/Projects/seattle/trunk/test/namespace.py", line 1487, in wrapped_function
    "/Users/adadgar/Projects/seattle/trunk/test/virtual_namespace.py", line 116, in evaluate
    "/Users/adadgar/Projects/seattle/trunk/test/safe.py", line 304, in safe_run
    "testxmlrpc_common", line 254, in <module>
    "/Users/adadgar/Projects/seattle/trunk/test/safe.py", line 174, in fnc

  User traceback:
    "dylink.repy", line 472, in <module>
    "dylink.repy", line 360, in dylink_dispatch
    "dylink.repy", line 455, in evaluate
    "testxmlrpc_common", line 254, in <module>

  Unsafe call: ('__import__',)
  ---
  """
  # exc_info() gives the traceback (see the traceback module for info)
  exceptiontype, exceptionvalue, exceptiontraceback = sys.exc_info()

  # Check if there is an exception
  if exceptiontype is None:
    return None

  # We store a full traceback, and a "filtered" user traceback to help the user
  full_tb = ""
  filtered_tb = ""

  for (filename, lineno, modulename, _) in traceback.extract_tb(exceptiontraceback):
    # linedata is always empty because we prevent the linecache from working
    # for safety reasons...

    # Check that this module is not black-listed
    skip = False

    # Check if any of the forbidden modules are a substring of the file name
    # e.g. if the name is /home/person/seattle/repy.py, we want to see 
    # that repy.py and skip this frame.
    for forbidden in TB_SKIP_MODULES:
      if forbidden in filename:
        skip = True
        break

    # Construct a frame of output.
    # Adjust traceback line numbers, see SeattleTestbed/repy_v2#95.
    stack_frame = '  "' + filename + '", line ' + str(lineno) + ", in " +\
        modulename + "\n"

    # Always add to the full traceback
    full_tb += stack_frame

    # If this module is not blacklisted, add it to the filtered traceback
    if not skip:
      filtered_tb += stack_frame


  # Construct the debug string
  debug_str = "---\nFollowing is a full traceback, and a user traceback.\n" \
              "The user traceback excludes non-user modules. The most recent call is displayed last.\n\n"

  debug_str += "Full debugging traceback:\n" + full_tb + "\n"
  debug_str += "User traceback:\n" + filtered_tb + "\n"

  # When I try to print an Exception object, I get:
  # "<type 'exceptions.Exception'>".   I'm going to look for this and produce
  # more sensible output if it happens.
  if exceptiontype is exception_hierarchy.CheckNodeException:
    debug_str += "Unsafe call with line number / type: " + str(exceptionvalue)
  elif exceptiontype is exception_hierarchy.CheckStrException:
    debug_str += "Unsafe string on line number / string: " + str(exceptionvalue)
  elif exceptiontype is exception_hierarchy.RunBuiltinException:
    debug_str += "Unsafe call: " + str(exceptionvalue)
  elif str(exceptiontype)[0] == '<':
    debug_str += "Exception (with "+str(exceptiontype)[1:-1]+"): " + str(exceptionvalue)
  else:
    debug_str += "Exception (with type "+str(exceptiontype)+"): " + str(exceptionvalue)

  debug_str += "\n---"

  # Clear the exception being handled
  try:
    sys.exc_clear()
  except:
    pass

  # Return the debug string
  return debug_str


# This function is called when there is an uncaught exception prior to exiting
def handle_exception():
  # Get the debug string
  debug_str = format_exception()

  # Print "Uncaught exception!", followed by the debug string
  print("---\nUncaught exception!\n",debug_str) 



def handle_internalerror(error_string, exitcode):
  """
  <Author>
    Brent Couvrette
  <Purpose>
    When an internal error happens in repy it should be handled differently 
    than normal exceptions, because internal errors could possibly lead to
    security vulnerabilities if we aren't careful.  Therefore when an internal
    error occurs, we will not return control to the user's program.  Instead
    we will log the error to the service log if available, then terminate.
  <Arguments>
    error_string - The error string to be logged if logging is enabled.
    exitcode - The exit code to be used in the harshexit call.
  <Exceptions>
    None
  <Side Effects>
    The program will exit.
  <Return>
    Shouldn't return because harshexit will always be called.
  """
  pass
# if servicelog:
#   import servicelogger

# try:
#   print("Internal Error")
#   handle_exception()
#   if not servicelog:
#     # If the service log is disabled, lets just exit.
#     harshexit.harshexit(exitcode)
#   else:
#     # Internal errors should not be given to the user's code to be caught,
#     # so we print the exception to the service log and exit. -Brent
#     exceptionstring = "[INTERNAL ERROR] " + error_string + '\n'
#     for line in traceback.format_stack():
#       exceptionstring = exceptionstring + line
# 
#     # This magic is determining what directory we are in, so that can be
#     # used as an identifier in the log.  In a standard deployment this
#     # should be of the form vXX where XX is the vessel number.  We don't
#     # want any exceptions here preventing us from exitting, so we will
#     # wrap this in a try-except block, and use a default value if we fail.
#     try:
#       identifier = os.path.basename(os.getcwd())
#     except:
#       # We use a blank except because if we don't, the user might be able to
#       # handle the exception, which is unacceptable on internal errors.  Using
#       # the current pid should avoid any attempts to write to the same file at
#       # the same time.
#       identifier = str(os.getpid())
#     else:
#       if identifier == '':
#         # If the identifier is blank, use the PID.
#         identifier = str(os.getpid())
#   
#     # Again we want to ensure that even if we fail to log, we still exit.
#     try:
#       servicelogger.multi_process_log(exceptionstring, identifier, logdirectory)
#     except Exception as e:
#       # if an exception occurs, log it (unfortunately, to the user's log)
#       print('Inner abort of servicelogger')
#       print(e,type(e))
#       traceback.print_exc()
#     finally:
#       harshexit.harshexit(exitcode)

# except Exception as e:
#   # if an exception occurs, log it (unfortunately, to the user's log)
#   print('Outer abort of servicelogger')
#   print(e,type(e))
#   traceback.print_exc()
# finally:
#   harshexit.harshexit(842)
