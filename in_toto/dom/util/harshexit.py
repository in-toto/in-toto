# harshexit module -- Should be renamed, but I'm not sure what to.
# Provides these functions:
#   portablekill: kill a function by pid
#   harshexit: die, and do some things depending on the error code
#   init_ostype: sets the module globals ostype and osrealtype

# used to get information about the system we're running on
import platform
import os
import sys

# needed for signal numbers
import signal

# This prevents writes to the nanny's status information after we want to stop

ostype = None
osrealtype = None

# this indicates if we are exiting.   Wrapping in a list to prevent needing a
# global   (the purpose of this is described below)
statusexiting = [False]


class UnsupportedSystemException(Exception):
  pass


def portablekill(pid):
  global ostype
  global osrealtype

  if ostype == None:
    init_ostype()

  if ostype == 'Linux' or ostype == 'Darwin':
    try:
      os.kill(pid, signal.SIGTERM)
    except:
      pass

    try:
      os.kill(pid, signal.SIGKILL)
    except:
      pass

  elif ostype == 'Windows':
    # Use new api
    os.kill(pid, signal.SIGKILL)
    
  else:
    raise UnsupportedSystemException("Unsupported system type: '"+osrealtype+"' (alias: "+ostype+")")



# exit all threads
def harshexit(val):
  global ostype
  global osrealtype

  if ostype == None:
    init_ostype()

  # The problem is that there can be multiple calls to harshexit before we
  # stop.   For example, a signal (like we may send to kill) may trigger a 
  # call.   As a result, we block all other status writers the first time this
  # is called, but don't later on...
  if not statusexiting[0]:

    # do this once (now)
    statusexiting[0] = True

  
    # we are stopped by the stop file watcher, not terminated through another 
    # mechanism
    if val == 4:
      # we were stopped by another thread.   Let's exit
      pass
    

    # We intentionally do not release the lock.   We don't want anyone else 
    # writing over our status information (we're killing them).
    

  if ostype == 'Linux':
    # The Nokia N800 refuses to exit on os._exit() by a thread.   I'm going to
    # signal our pid with SIGTERM (or SIGKILL if needed)
    portablekill(os.getpid())
#    os._exit(val)
  elif ostype == 'Darwin':
    os._exit(val)
  elif ostype == 'Windows':
    # stderr is not automatically flushed in Windows...
    sys.stderr.flush()
    os._exit(val)
  else:
    raise UnsupportedSystemException("Unsupported system type: '"+osrealtype+"' (alias: "+ostype+")")



# Figure out the OS type
def init_ostype():
  global ostype
  global osrealtype

  # figure out what sort of system we are...
  osrealtype = platform.system()

  # The Nokia N800 (and N900) uses the ARM architecture, 
  # and we change the constants on it to make disk checks happen less often 
  if osrealtype == 'Linux' or osrealtype == 'Windows' or osrealtype == 'Darwin':
    ostype = osrealtype
    return

  # workaround for a Vista bug...
  if osrealtype == 'Microsoft':
    ostype = 'Windows'
    return

  if osrealtype == 'FreeBSD':
    ostype = 'Linux'
    return

  if osrealtype.startswith('CYGWIN'):
    # I do this because ps doesn't do memory info...   They'll need to add
    # pywin to their copy of cygwin...   I wonder if I should detect its 
    # abscence and tell them (but continue)?
    ostype = 'Windows'
    return

  ostype = 'Unknown'
