import logging
from simple_settings import settings

logging.basicConfig(level=settings.LOG_LEVEL, format='%(message)s')

def doing(msg):
  logging.info("DOING:   %s" % str(msg))

def passing(msg):
  logging.info("PASSING: %s" % str(msg))

def warning(msg):
  logging.warn("WARNING: %s" % str(msg))

def failing(msg):
  logging.warn("FAILING: %s" % str(msg))