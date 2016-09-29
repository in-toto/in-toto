import os
import json

import toto.ssl_crypto.keys
import toto.models.layout as m


def create_and_persist_or_load_key(filename):
  if not os.path.isfile(filename):
    key_dict = toto.ssl_crypto.keys.generate_rsa_key()
    with open(filename, "w+") as fp:
      key_data = toto.ssl_crypto.keys.format_keyval_to_metadata(
          key_dict["keytype"], key_dict["keyval"], private=True)
      fp.write(json.dumps(key_data))
      return key_dict
  else:
    with open(filename, "r") as fp:
      return toto.ssl_crypto.keys.format_metadata_to_key(json.load(fp))

def main():

  # Get keys
  alice_key = create_and_persist_or_load_key("alice")
  bob_key = create_and_persist_or_load_key("bob")


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



