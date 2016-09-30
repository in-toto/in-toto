import os
import subprocess

import toto.ssl_crypto.keys
import toto.models.layout as m
import toto.util


def main():


  #############################################################################
  # Define the supply chain
  #############################################################################

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
        "name": "package",
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


  # Check if dumping - reading - dumping produces the same layout
  # layout_same = m.Layout.read_from_file("root.layout")
  # if repr(layout) != repr(layout_same):
  #   print "There is something wrong with layout de-/serialization"


  #############################################################################
  # Do the supply chain
  #############################################################################

  write_code_cmd = "python -m toto.toto-run "\
                   "--name write-code --products foo.py "\
                   "--key alice -- vi foo.py"
  subprocess.call(write_code_cmd.split())

  package_cmd = "python -m toto.toto-run "\
                "--name package --material foo.py --products foo.tar.gz "\
                "--key bob --record-byproducts -- tar zcvf foo.tar.gz foo.py"
  subprocess.call(package_cmd.split())

  #############################################################################
  # Verify the supply chain
  #############################################################################


if __name__ == '__main__':
  main()



