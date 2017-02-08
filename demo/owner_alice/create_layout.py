from in_toto.util import import_rsa_key_from_file
from in_toto.models.layout import Layout

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
        "name": "clone",
        "material_matchrules": [],
        "product_matchrules": [["CREATE", "demo-project/foo.py"]],
        "pubkeys": [key_bob["keyid"]],
        "expected_command": "git clone git@github.com:in-toto/demo-project.git",
      },{
        "name": "update-version",
        "material_matchrules": [["MATCH", "PRODUCT", "demo-project/*", "FROM", "clone"]],
        # FIXME: CREATE is more like an allow here, is fixed in next version
        "product_matchrules": [["CREATE", "demo-project/foo.py"]],
        "pubkeys": [key_bob["keyid"]],
        "expected_command": "",
      },{
        "name": "package",
        "material_matchrules": [
            ["MATCH", "demo-project/*", "WITH", "PRODUCTS", "FROM", "update-version"],
        ],
        "product_matchrules": [
            ["CREATE", "demo-project.tar.gz"],
        ],
        "pubkeys": [key_carl["keyid"]],
        "expected_command": "tar --exclude '.git' -zcvf demo-project.tar.gz demo-project",
      }],
    "inspect": [{
        "name": "untar",
        "material_matchrules": [
            ["MATCH", "demo-project.tar.gz", "WITH", "PRODUCTS", "FROM", "package"],
            # FIXME: Without the "allow everything else" rule here
            # inspection would fail because of the metadata and other files
            # (.DS_STORE, layout key, ...) in the directory where the Inspection
            # is executed, which get recorded as materials.
            # The behavior is actually wanted in order to prevent sneaking
            # files. But we do have to think of a way to ignore
            # irrelevant files.
            ["ALLOW", "*"],
        ],
        "product_matchrules": [
            ["MATCH", "demo-project/foo.py", "WITH", "PRODUCTS", "FROM", "update-version"],
            # FIXME: See material_matchrules above
            ["ALLOW", "*"],

        ],
        "run": "tar xzf demo-project.tar.gz",
      }],
    "signatures": []
  })

  # Sign and dump layout to "layout.root"
  layout.sign(key_alice)
  layout.dump()

if __name__ == '__main__':
  main()