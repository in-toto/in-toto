"""
Configure base logger for in_toto (see in_toto.log for details).

"""
import in_toto.log
from securesystemslib import KEY_TYPE_RSA, KEY_TYPE_ED25519

SUPPORTED_KEY_TYPES = [KEY_TYPE_RSA, KEY_TYPE_ED25519]


# in-toto version
__version__ = "1.0.1"
