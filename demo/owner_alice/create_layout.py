from toto.util import import_rsa_key_from_file
from toto.models.layout import Layout

def main():
  # Load Alice's private key to later sign the layout
  key_alice = import_rsa_key_from_file("alice")
  # Fetch and load Bob's and Carl's public keys
  # to specify that they are athorized to perform certain step in the layout
  key_bob = import_rsa_key_from_file("../functionary_bob/bob.pub")
  key_carl = import_rsa_key_from_file("../functionary_carl/carl.pub")

  layout = Layout.read({
    "_type": "layout",
    "keys": {
        key_bob["keyid"]: key_bob,
        key_carl["keyid"]: key_carl,
    },
    "steps": [{
        "name": "write-code",
        "material_matchrules": [],
        "product_matchrules": [["CREATE", "foo.py"]],
        "pubkeys": [key_bob["keyid"]],
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
        "pubkeys": [key_carl["keyid"]],
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
        "run": "tar xfz foo.tar.gz",
      }],
    "signatures": []
  })

  # Sign and dump layout to "layout.root"
  layout.sign(key_alice)
  layout.dump()

if __name__ == '__main__':
  main()