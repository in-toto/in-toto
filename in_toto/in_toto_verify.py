#!/usr/bin/env python
"""
<Program Name>
  in_toto_verify.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Oct 3, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides a command line interface for verifylib.in_toto_verify.

<Return Codes>
  2 if an exception occurred during argument parsing
  1 if an exception occurred (verification failed)
  0 if no exception occurred (verification passed)

"""
import sys
import argparse
import logging

from in_toto import verifylib
from in_toto.common_args import (GPG_HOME_ARGS, GPG_HOME_KWARGS, VERBOSE_ARGS,
    VERBOSE_KWARGS, QUIET_ARGS, QUIET_KWARGS, title_case_action_groups,
    sort_action_groups)
from in_toto.models.metadata import Metablock
from in_toto import (
    __version__, SUPPORTED_KEY_TYPES, KEY_TYPE_RSA, KEY_TYPE_ED25519)
from securesystemslib import interface
from securesystemslib.gpg import functions as gpg_interface

# Command line interfaces should use in_toto base logger (c.f. in_toto.log)
LOG = logging.getLogger("in_toto")

def create_parser():
  """Create and return configured ArgumentParser instance. """
  parser = argparse.ArgumentParser(
      formatter_class=argparse.RawDescriptionHelpFormatter,
      description="""
in-toto-verify is the main verification tool of the suite, and it is used to
verify that the software supply chain of the delivered product was carried out
as defined in the passed in-toto supply chain layout. Evidence for supply chain
steps must be available in the form of link metadata files named
'<step name>.<functionary keyid prefix>.link'.

Both 'in-toto-run' and 'in-toto-record' generate link metadata named in this
manner. If you require special handling of the in-toto link metadata files,
please take a look at the library api to modify this behavior.

The verification includes the following checks:
  * the layout is signed with the passed keys,
  * the layout has not expired,
  * a threshold of link metadata files exists for each step of the layout,
  * link files are signed by the authorized functionaries,
  * the materials and products for each step, as reported by the corresponding
    link files, adhere to the artifact rules specified by the step.

Additionally, inspection commands defined in the layout are executed
sequentially, followed by processing the inspections' artifact rules.

If the layout includes sublayouts, the verification routine will recurse into a
subdirectory named '<step name>.<keyid prefix>', where all the links relevant
to that sublayout must exist. The sublayout itself must be in the same
directory as the other links of the superlayout. (i.e. '<step name>.<keyid
prefix>.link')

The command returns 2 if it is called with wrong arguments, 1 if in-toto
verification fails and 0 if verification passes. """)

  parser.usage = "%(prog)s <named arguments> [optional arguments]"

  parser.epilog = """EXAMPLE USAGE

Verify supply chain in 'root.layout', signed with private part of
'key_file.pub'.

  {prog} --layout root.layout --layout-keys key_file.pub


Verify supply chain as above but load links corresponding to steps of
'root.layout' from 'link_dir'.

  {prog} --layout root.layout --layout-keys key_file.pub \\
      --link-dir link_dir


Verify supply chain in 'root.layout', signed with GPG key '...7E0C8A17',
for which the public part can be found in the GPG keyring at '~/.gnupg'.

  {prog} --layout root.layout \\
      --gpg 8465A1E2E0FB2B40ADB2478E18FB3F537E0C8A17 \\
      --gpg-home ~/.gnupg


""".format(prog=parser.prog)


  named_args = parser.add_argument_group("required named arguments")

  named_args.add_argument("-l", "--layout", type=str, required=True,
      metavar="<path>", help=(
      "path to root layout specifying the software supply chain to be"
      " verified."))

  named_args.add_argument("-k", "--layout-keys", type=str, metavar="<path>",
      nargs="+", help=(
      "paths to public key files used to verify the passed root layout's"
      " signatures. See '--key-types' for available formats. Passing at least"
      " one key using '--layout-keys' and/or '--gpg' is required. For each"
      " passed key the layout must carry a valid signature."))

  parser.add_argument("-t", "--key-types", dest="key_types",
      type=str, choices=SUPPORTED_KEY_TYPES,
      nargs="+", help=(
      "types of keys specified by the '--layout-keys' option. '{rsa}' keys are"
      " expected in a 'PEM' format and '{ed25519}' in a custom"
      " 'securesystemslib/json' format. If multiple keys are passed via"
      " '--layout-keys' the same amount of key types must be passed. Key"
      " types are then associated with keys by index. If '--key-types' is"
      " omitted, the default of '{rsa}' is used for all keys.".format(
      rsa=KEY_TYPE_RSA, ed25519=KEY_TYPE_ED25519)))

  named_args.add_argument("-g", "--gpg", nargs="+", metavar="<id>",
      help=(
      "GPG keyid, identifying a public key in the GPG keyring used to verify"
      " the passed root layout's signatures."
      " Passing at least one key using '--layout-keys' and/or '--gpg' is"
      " required. For each passed key the layout must carry a valid"
      " signature."))

  parser.add_argument("--link-dir", dest="link_dir", type=str,
      metavar="<path>", default=".", help=(
          "path to directory from which link metadata files for steps defined"
          " in the root layout should be loaded. If not passed, links are"
          " loaded from the current working directory."))

  parser.add_argument(*GPG_HOME_ARGS, **GPG_HOME_KWARGS)

  verbosity_args = parser.add_mutually_exclusive_group(required=False)
  verbosity_args.add_argument(*VERBOSE_ARGS, **VERBOSE_KWARGS)
  verbosity_args.add_argument(*QUIET_ARGS, **QUIET_KWARGS)

  parser.add_argument('--version', action='version',
                      version='{} {}'.format(parser.prog, __version__))

  title_case_action_groups(parser)
  sort_action_groups(parser)

  return parser

def main():
  """Parse arguments and call in_toto_verify. """
  parser = create_parser()
  args = parser.parse_args()

  LOG.setLevelVerboseOrQuiet(args.verbose, args.quiet)

  # For verifying at least one of --layout-keys or --gpg must be specified
  # Note: Passing both at the same time is possible.
  if (args.layout_keys is None) and (args.gpg is None):
    parser.print_help()
    parser.error("wrong arguments: specify at least one of"
        " '--layout-keys path [path ...]' or '--gpg id [id ...]'")

  try:
    LOG.info("Loading layout...")
    layout = Metablock.load(args.layout)

    layout_key_dict = {}
    if args.layout_keys is not None:
      LOG.info("Loading layout key(s)...")
      layout_key_dict.update(
          interface.import_publickeys_from_file(
              args.layout_keys, args.key_types))

    if args.gpg is not None:
      LOG.info("Loading layout gpg key(s)...")
      layout_key_dict.update(
          gpg_interface.export_pubkeys(
              args.gpg, homedir=args.gpg_home))

    verifylib.in_toto_verify(layout, layout_key_dict, args.link_dir)

  except Exception as e:
    LOG.error("(in-toto-verify) {0}: {1}".format(type(e).__name__, e))
    sys.exit(1)

  sys.exit(0)


if __name__ == "__main__":
  main()
