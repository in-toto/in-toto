import os

import toto.ssl_crypto.keys
import toto.models.layout as m
import toto.util


def main():

  # Get keys
  alice_key = toto.util.create_and_persist_or_load_key("alice")
  bob_key = toto.util.create_and_persist_or_load_key("bob")


  # Create Layout
  layout = m.Layout.read({ 
    "_type": "layout",
    "expires": "EXPIRES",
    "keys": {
        alice_key["keyid"]: alice_key,
        bob_key["keyid"]: bob_key
    },
    "steps": [{
        "name": "write-code",
        "material_matchrules": [],
        "product_matchrules": [["CREATE", "foo.py"]],
        "pubkeys": [alice_key["keyid"]],
        "expected_command": "vi",
      },
      {
        "_name": "package",
        "material_matchrules": [
            ["MATCH", "PRODUCT", "foo.py", "FROM", "write-code"],
        ],
        "product_matchrules": [
            ["CREATE", "foo.tar.gz"],
        ],
        "pubkeys": [bob_key["keyid"]],
        "expected_command": "tar zcvf foo.tar.gz foo.py",
      }],
    "inspect": [{
        "name": "untar",
        "material_matchrules": [
            ["MATCH", "PRODUCT", "foo.tar.gz", "FROM", "package"]
        ],
        "product_matchrules": [
            ["MATCH", "PRODUCT", "foo.py", "FROM", "write-code"],
        ],
        "run": "inspect_tarball.sh foo.tar.gz",
      }],
    "signatures": []
  })

  # Sign and dump layout
  layout.sign(alice_key)
  layout.dump()

  # Load layout
  m.Layout.read_from_file("root.layout")
  # #(Verify signature)

  # Dump again with different name 
  layout.dump(filename="same.layout")


if __name__ == '__main__':
  main()



