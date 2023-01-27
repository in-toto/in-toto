# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
Configure base logger for in_toto (see in_toto.log for details).

"""
import in_toto.log
from securesystemslib import KEY_TYPE_RSA, KEY_TYPE_ED25519, KEY_TYPE_ECDSA

SUPPORTED_KEY_TYPES = [KEY_TYPE_RSA, KEY_TYPE_ED25519, KEY_TYPE_ECDSA]


# in-toto version
__version__ = "1.3.0"
