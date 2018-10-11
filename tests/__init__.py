import in_toto
import logging

# Override in-toto logger default StreamHandler to prevent test log inundation
in_toto.log.logger.handlers = [logging.NullHandler()]
