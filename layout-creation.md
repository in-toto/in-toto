# Layout Creation Example

The following Python snippet shows how to use in-toto to create a software
supply chain layout like the one that is used for the in-toto demo.
*Take a look at the [demo repo](https://github.com/in-toto/demo) for more
information about that supply chain*.


```python
from securesystemslib.interface import (generate_and_write_rsa_keypair,
    import_rsa_privatekey_from_file)
from in_toto.models.layout import Layout, Step, Inspection
from in_toto.models.metadata import Metablock

# Create RSA private and public keys

# Alice is the project owner and her private key is used to sign the layout
alice_path = generate_and_write_rsa_keypair("alice", password="123")
alice_key = import_rsa_privatekey_from_file(alice_path, password="123")

# Bob and Carl are both functionaries, i.e. they are authorized to carry out
# different steps of the supply chain. Their public keys are added to the
# supply chain layout, in order to verify the signatures of the link metadata
# that Bob and Carl will generate when carrying out their respective tasks.
bob_path = generate_and_write_rsa_keypair("bob", password="123")
carl_path = generate_and_write_rsa_keypair("carl", password="123")


# Create an empty layout
layout = Layout()

# Add functionary public keys to the layout
bob_pubkey = layout.add_functionary_key_from_path(bob_path + ".pub")
carl_pubkey = layout.add_functionary_key_from_path(carl_path + ".pub")

# Set expiration date so that the layout will expire in 4 months
layout.set_relative_expiration(months=4)


# Create layout steps

# Each step describes a task that is required to be carried out in this supply
# chain. A step must have a unique name to associate the related link metadata
# (i.e. the evidence that the step was carried out). Additionally, each step
# should list rules, about the present related files before and after the step
# was carried out. A steps pubkeys field lists the keyids of functionaries
# authorized to perform the step.
step_clone = Step(name="clone")
step_clone.set_expected_command_from_string(
    "git clone https://github.com/in-toto/demo-project.git")
step_clone.add_product_rule_from_string("CREATE demo-project/foo.py")
step_clone.add_product_rule_from_string("DISALLOW *")
step_clone.pubkeys = [bob_pubkey["keyid"]]

step_update = Step(name="update-version")
step_update.add_material_rule_from_string(
    "MATCH demo-project/* WITH PRODUCTS FROM clone")
step_update.add_material_rule_from_string("DISALLOW *")
step_update.add_product_rule_from_string("ALLOW demo-project/foo.py")
step_update.add_product_rule_from_string("DISALLOW *")
step_update.pubkeys = [bob_pubkey["keyid"]]

step_package = Step(name="package")
step_package.set_expected_command_from_string(
    "tar --exclude '.git' -zcvf demo-project.tar.gz demo-project")
step_package.add_material_rule_from_string(
    "MATCH demo-project/* WITH PRODUCTS FROM update-version")
step_package.add_material_rule_from_string("DISALLOW *")
step_package.add_product_rule_from_string("CREATE demo-project.tar.gz")
step_package.add_product_rule_from_string("DISALLOW *")
step_package.pubkeys = [carl_pubkey["keyid"]]


# Create inspection

# Inspections are commands that are executed upon in-toto final product
# verification. In this case, we define an inspection that expands the final
# product and verifies that the contents of the archive match with what was
# put into the archive.
inspection = Inspection(name="untar")
inspection.set_run_from_string("tar xzf demo-project.tar.gz")
inspection.add_material_rule_from_string(
    "MATCH demo-project.tar.gz WITH PRODUCTS FROM package")
inspection.add_product_rule_from_string(
    "MATCH demo-project/foo.py WITH PRODUCTS FROM update-version")


# Add steps and inspections to layout
layout.steps = [step_clone, step_update, step_package]
layout.inspect = [inspection]


# Eventually the layout gets wrapped in a generic in-toto metablock, which
# provides functions to sign the metadata contents and write them to a file.
metablock = Metablock(signed=layout)
metablock.sign(alice_key)
metablock.dump("root.layout")

```