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
        "expected_command": "git clone https://github.com/in-toto/demo-project.git",
      },{
        "name": "update-version",
        "material_matchrules": [["MATCH", "demo-project/*", "WITH", "PRODUCTS", "FROM", "clone"]],
        # FIXME: CREATE is more like an allow here, is fixed in next version
        "product_matchrules": [["ALLOW", "demo-project/foo.py"]],
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
            # FIXME: If the routine running inspections would gather the
            # materials/products to record from the rules we wouldn't have to
            # ALLOW other files that we aren't interested in.
            ["ALLOW", ".keep"],
            ["ALLOW", "alice.pub"],
            ["ALLOW", "root.layout"],
        ],
        "product_matchrules": [
            ["MATCH", "demo-project/foo.py", "WITH", "PRODUCTS", "FROM", "update-version"],
            # FIXME: See material_matchrules above
            ["ALLOW", "demo-project/.git/*"],
            ["ALLOW", "demo-project.tar.gz"],
            ["ALLOW", ".keep"],
            ["ALLOW", "alice.pub"],
            ["ALLOW", "root.layout"],
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