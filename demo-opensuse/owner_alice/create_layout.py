from in_toto.util import import_rsa_key_from_file
from in_toto.models.layout import Layout

def main():
  # Load Alice's private key to later sign the layout
  key_alice = import_rsa_key_from_file("alice")
  # Fetch and load Bob's and Carl's public keys
  # to specify that they are authorized to perform certain step in the layout
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
        "product_matchrules": [["CREATE", "home:shikher/connman/_service"],
            ["CREATE", "home:shikher/connman/connman-1.30.tar.gz"],
            ["CREATE", "home:shikher/connman/connman-1.30.tar.sign"],
            ["CREATE", "home:shikher/connman/connman-rpmlintrc"],
            ["CREATE", "home:shikher/connman/connman.changes"],
            ["CREATE", "home:shikher/connman/connman.keyring"],
            ["CREATE", "home:shikher/connman/connman.spec"]],
        "pubkeys": [key_bob["keyid"]],
        "expected_command": "git clone https://github.com/shikherverma/connman.git",
        "threshold": 1,
      },{
        "name": "update-changelog",
        "material_matchrules": [["MATCH", "home:shikher/connman/connman.changes", "WITH", "PRODUCTS", "FROM", "clone"]],
        # FIXME: CREATE is more like an allow here, is fixed in next version
        "product_matchrules": [["ALLOW", "home:shikher/connman/connman.changes"]],
        "pubkeys": [key_bob["keyid"]],
        "expected_command": "",
        "threshold": 1,
      },{
        "name": "test",
        "material_matchrules": [],
        "product_matchrules": [],
        "pubkeys": [key_carl["keyid"]],
        "expected_command": "osc build openSUSE_Factory x86_64 connman/connman.spec",
        "threshold": 1,
      },{
        "name": "package",
        "material_matchrules": [
            ["MATCH", "home:shikher/connman/_service", "WITH", "PRODUCTS", "FROM", "clone"],
            ["MATCH", "home:shikher/connman/connman-1.30.tar.gz", "WITH", "PRODUCTS", "FROM", "clone"],
            ["MATCH", "home:shikher/connman/connman-1.30.tar.sign", "WITH", "PRODUCTS", "FROM", "clone"],
            ["MATCH", "home:shikher/connman/connman-rpmlintrc", "WITH", "PRODUCTS", "FROM", "clone"],
            ["MATCH", "home:shikher/connman/connman.changes", "WITH", "PRODUCTS", "FROM", "update-changelog"],
            ["MATCH", "home:shikher/connman/connman.keyring", "WITH", "PRODUCTS", "FROM", "clone"],
            ["MATCH", "home:shikher/connman/connman.spec", "WITH", "PRODUCTS", "FROM", "clone"],
        ],
        "product_matchrules": [
            ["CREATE", "connman-1.30-1.1.src.rpm"],
        ],
        "pubkeys": [key_carl["keyid"]],
        "expected_command": "",
        "threshold": 1,
      }],
    "inspect": [{
        "name": "unpack",
        "material_matchrules": [
            ["MATCH", "connman-1.30-1.1.src.rpm", "WITH", "PRODUCTS", "FROM", "package"],
            # FIXME: If the routine running inspections would gather the
            # materials/products to record from the rules we wouldn't have to
            # ALLOW other files that we aren't interested in.
            ["ALLOW", ".keep"],
            ["ALLOW", "alice.pub"],
            ["ALLOW", "root.layout"],
        ],
        "product_matchrules": [
            ["MATCH", "connman-1.30-1.1.src.rpm", "WITH", "PRODUCTS", "FROM", "package"],
            ["MATCH", "connman-1.30.tar.gz", "WITH", "PRODUCTS", "IN", "home:shikher/connman", "FROM", "clone"],
            ["MATCH", "_service", "WITH", "PRODUCTS", "IN", "home:shikher/connman", "FROM", "clone"],
            ["MATCH", "connman-1.30.tar.sign", "WITH", "PRODUCTS", "IN", "home:shikher/connman", "FROM", "clone"],
            ["MATCH", "connman-rpmlintrc", "WITH", "PRODUCTS", "IN", "home:shikher/connman", "FROM", "clone"],
            ["MATCH", "connman.changes", "WITH", "PRODUCTS", "IN", "home:shikher/connman", "FROM", "update-changelog"],
            ["MATCH", "connman.keyring", "WITH", "PRODUCTS", "IN", "home:shikher/connman", "FROM", "clone"],
            # FIXME: very weird that hash doesn't match for this file
            ["ALLOW", "connman.spec"],
            ["ALLOW", ".keep"],
            ["ALLOW", "alice.pub"],
            ["ALLOW", "root.layout"],
        ],
        "run": "unrpm connman-1.30-1.1.src.rpm",
      }],
    "signatures": []
  })

  # Sign and dump layout to "layout.root"
  layout.sign(key_alice)
  layout.dump()

if __name__ == '__main__':
  main()
