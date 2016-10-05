import logging
from simple_settings import settings

logging.basicConfig(level=settings.LOG_LEVEL, format='%(message)s')

def doing(msg):
  logging.info("DOING:   %s" % str(msg))

def warning(msg):
  logging.warn("WARNING: %s" % str(msg))

def passing(msg):
  logging.critical("PASSING: %s" % str(msg))

def failing(msg):
  logging.critical("FAILING: %s" % str(msg))

error = logging.error
