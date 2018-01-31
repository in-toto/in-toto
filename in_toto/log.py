"""
<Program Name>
  log.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Oct 4, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Configures "in_toto" base logger, which can be used for debugging and user
  feedback in in-toto command line interfaces and libraries.

  Logging methods and levels are available through Python's logging module.

  If the log level is set to 'logging.DEBUG' log messages include
  additional information about the log statement. Moreover, calls to the
  `error` method will also output a stacktrace (if available).
  In all other log levels only the log message is shown without additional
  info.

  The default log level of the base logger is 'logging.WARNING', unless
  'in_toto.settings.DEBUG' is 'True', in that case the default log level is
  'logging.DEBUG'.

  The default handler of the base logger is a 'StreamHandler', which writes all
  log messages permitted by the used log level to 'sys.stderr'.


<Usage>
  This module should be imported in '__init__.py' to configure the base logger.
  Subsequently, command line interfaces should fetch the base logger by name
  and customize the log level according to any passed command line arguments.
  They can use the convenience method `setLevelVerboseOrQuiet` available on
  the custom base logger, e.g.:

  ```
  import logging
  log = logging.getLogger("in_toto")

  # parse args ...

  log.setLevelVerboseOrQuiet(args.verbose, args.quiet)

  # call library function ...
  ```

  Library modules can then create loggers, passing the module name, which will
  inherit the base logger's log level and format, e.g.:

  ```
  import logging
  log = logging.getLogger(__name__)

  log.warning("Shown per default.")

  log.info("Only shown if, log level was set to <= logging.INFO, e.g. in cli.")

  log.info("In debug mode it looks something like this)
  # in_toto.runlib:400:INFO:In debug mode it looks something like this

  ```

"""
import sys
import logging
import in_toto.settings



# Different log message formats for different log levels
_FORMAT_MESSAGE = "%(message)s"
_FORMAT_DEBUG = "%(name)s:%(lineno)d:%(levelname)s:%(message)s"

# Cache default logger class, should be logging.Logger if not changed elsewhere
_logger_class = logging.getLoggerClass()

# Create logger subclass
class InTotoLogger(_logger_class):
  """logger.Logging subclass, using providing custom error method and
  convenience method for log levels. """

  QUIET = logging.CRITICAL + 1

  def error(self, msg):
    """Show stacktrace depending on its availability and the logger's log
    level, i.e. only show stacktrace in DEBUG level. """
    show_stacktrace = (self.level == logging.DEBUG and
        sys.exc_info() != (None, None, None))
    return super(InTotoLogger, self).error(msg, exc_info=show_stacktrace)

  def setLevelVerboseOrQuiet(self, verbose, quiet):
    """Convenience method to set the logger's verbosity level based on the
    passed booleans verbose and quiet (useful for cli tools). """
    if verbose:
      self.setLevel(logging.INFO)

    elif quiet:
      # TODO: Is it enough to use logging.CRITICAL + 1 to suppress all output?
      # A saver way would be to use a NullHandler or Filters.
      self.setLevel(self.QUIET)


# Temporarily change logger default class to instantiate an in-toto base logger
logging.setLoggerClass(InTotoLogger)
logger = logging.getLogger("in_toto")
logging.setLoggerClass(_logger_class)

# In DEBUG mode we log all log types and add additional information,
# otherwise we only log warning, error and critical and only the message.
if in_toto.settings.DEBUG: # pragma: no cover
  level = logging.DEBUG
  format_string = _FORMAT_DEBUG

else:
  level = logging.WARNING
  format_string = _FORMAT_MESSAGE

# Add a StreamHandler with the chosen format to in-toto's base logger,
# which will write log messages to `sys.stderr`.
formatter = logging.Formatter(format_string)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(level)
