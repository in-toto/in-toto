#!/usr/bin/env python
import os
from designlib import toto_prompt

if __name__ == "__main__":
    os.environ["SIMPLE_SETTINGS"]="toto.settings"
    toto_prompt()
