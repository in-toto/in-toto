# Copyright New York University and the in-toto contributors
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  in_toto_run.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  June 27, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides a command line interface for runlib.in_toto_run.

<Return Codes>
  2 if an exception occurred during argument parsing
  1 if an exception occurred
  0 if no exception occurred

"""

import argparse
import logging
import sys
from getpass import getpass

from in_toto import __version__, runlib
from in_toto.common_args import (
    BASE_PATH_ARGS,
    BASE_PATH_KWARGS,
    DSSE_ARGS,
    DSSE_KWARGS,
    EXCLUDE_ARGS,
    EXCLUDE_KWARGS,
    GPG_ARGS,
    GPG_HOME_ARGS,
    GPG_HOME_KWARGS,
    GPG_KWARGS,
    KEY_PASSWORD_ARGS,
    KEY_PASSWORD_KWARGS,
    LSTRIP_PATHS_ARGS,
    LSTRIP_PATHS_KWARGS,
    METADATA_DIRECTORY_ARGS,
    METADATA_DIRECTORY_KWARGS,
    OPTS_TITLE,
    QUIET_ARGS,
    QUIET_KWARGS,
    RUN_TIMEOUT_ARGS,
    RUN_TIMEOUT_KWARGS,
    SIGNING_KEY_ARGS,
    SIGNING_KEY_KWARGS,
    VERBOSE_ARGS,
    VERBOSE_KWARGS,
    parse_password_and_prompt_args,
    sort_action_groups,
    title_case_action_groups,
)
from in_toto.models._signer import load_crypto_signer_from_pkcs8_file

# Command line interfaces should use in_toto base logger (c.f. in_toto.log)
LOG = logging.getLogger("in_toto")


def create_parser():
    """Create and return configured ArgumentParser instance."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
in-toto-run is the main command line interface for generating link
metadata while carrying out a supply chain step. To do this, it wraps the
passed command, and attempts to track all relevant information about the
wrapped command's execution. It records paths and hashes of 'materials' (files
before command execution) and 'products' (files after command execution) and
writes them together with other information (executed command, return value,
stdout and stderr) to a link metadata file, which is signed with the passed
key. It returns a non-zero value on failure and zero otherwise.""",
    )

    parser.usage = f"%(prog)s <named arguments> [{OPTS_TITLE.lower()}] \\\n\t -- <command> [args]"

    parser.epilog = f"""EXAMPLE USAGE

Tag a git repo, storing files in CWD as products, signing the resulting link
file with the private key loaded from 'key_file'.

  {parser.prog} -n tag -p . --signing-key key_file -- git tag v1.0


Create a tarball, storing files in 'project' directory as materials and the
tarball as product, signing the link file with a GPG key '...7E0C8A17'.

  {parser.prog} -n package -m project -p project.tar.gz \\
         -g 8465A1E2E0FB2B40ADB2478E18FB3F537E0C8A17 \\
         -- tar czf project.tar.gz project


Not all supply chain steps require that a command be executed. in-toto can
still generate signed attestations, e.g. for review work. In that case, files
may be marked as materials for the manual review process and the command be
omitted.

  {parser.prog} -n review --signing-key key_file -m document.pdf -x


If an artifact that should be recorded is not in the current working directory
(or one of its subdirectories) it can be located using the base path option.
Note that in this example only the relative path, 'document.pdf' is stored
along with its hash in the resulting link metadata file.

  {parser.prog} -n review --signing-key key_file -m document.pdf \\
         --base-path /my/review/docs/ -x


Similarly, it is possible to pass the full path to the artifact that should
be recorded together with a left-strip path, to only store a relative path,
e.g. 'document.pdf'.

  {parser.prog} -n review --signing-key key_file \\
         -m /tmp/my/review/docs/document.pdf \\
         --lstrip-paths /tmp/my/review/docs/ -x


"""

    named_args = parser.add_argument_group("required named arguments")

    # FIXME: Do we limit the allowed characters for the name?
    named_args.add_argument(
        "-n",
        "--step-name",
        type=str,
        required=True,
        metavar="<name>",
        help=(
            "name for the resulting link metadata file, which is written to"
            " '<name>.<keyid prefix>.link'. It is also used to associate the link"
            " with a step defined in an in-toto layout."
        ),
    )

    parser.add_argument(
        "-m",
        "--materials",
        type=str,
        required=False,
        nargs="+",
        metavar="<path>",
        help=(
            "paths to files or directories, for which paths and hashes are stored in"
            " the resulting link metadata before the command is executed. Symlinks"
            " to files are followed."
        ),
    )

    parser.add_argument(
        "-p",
        "--products",
        type=str,
        required=False,
        nargs="+",
        metavar="<path>",
        help=(
            "paths to files or directories, for which paths and hashes are stored in"
            " the resulting link metadata after the command is executed. Symlinks to"
            " files are followed."
        ),
    )

    parser.add_argument(
        "-s",
        "--record-streams",
        dest="record_streams",
        default=False,
        action="store_true",
        help=(
            "duplicate 'stdout' and 'stderr' of the executed command and store the"
            " contents in the resulting link metadata. Do not use with interactive"
            " commands."
        ),
    )

    parser.add_argument(
        "-x",
        "--no-command",
        dest="no_command",
        default=False,
        action="store_true",
        help=(
            "generate link metadata without executing a command, e.g. for a"
            " signed-off-by step."
        ),
    )

    parser.add_argument(*KEY_PASSWORD_ARGS, **KEY_PASSWORD_KWARGS)

    named_args.add_argument(*GPG_ARGS, **GPG_KWARGS)
    parser.add_argument(*GPG_HOME_ARGS, **GPG_HOME_KWARGS)

    named_args.add_argument(*SIGNING_KEY_ARGS, **SIGNING_KEY_KWARGS)

    parser.add_argument(*EXCLUDE_ARGS, **EXCLUDE_KWARGS)
    parser.add_argument(*BASE_PATH_ARGS, **BASE_PATH_KWARGS)
    parser.add_argument(*LSTRIP_PATHS_ARGS, **LSTRIP_PATHS_KWARGS)
    parser.add_argument(*METADATA_DIRECTORY_ARGS, **METADATA_DIRECTORY_KWARGS)
    parser.add_argument(*DSSE_ARGS, **DSSE_KWARGS)
    parser.add_argument(*RUN_TIMEOUT_ARGS, **RUN_TIMEOUT_KWARGS)

    verbosity_args = parser.add_mutually_exclusive_group(required=False)
    verbosity_args.add_argument(*VERBOSE_ARGS, **VERBOSE_KWARGS)
    verbosity_args.add_argument(*QUIET_ARGS, **QUIET_KWARGS)

    # FIXME: This is not yet ideal.
    # What should we do with tokens like > or ; ?
    parser.add_argument(
        "link_cmd",
        nargs="*",
        metavar="<command>",
        help=(
            "command to be executed. It is separated from named and optional"
            " arguments by a double dash '--'."
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"{parser.prog} {__version__}",
    )

    title_case_action_groups(parser)
    sort_action_groups(parser)

    return parser


def main():
    """Parse arguments, load key from disk (prompts for password if key is
    encrypted) and call in_toto_run."""
    parser = create_parser()
    args = parser.parse_args()

    LOG.setLevelVerboseOrQuiet(args.verbose, args.quiet)

    # Use exactly one of gpg or pkcs8 signing key
    if sum([bool(args.gpg), bool(args.signing_key)]) != 1:
        parser.print_usage()
        parser.error(
            "Specify either '--signing-key <path>' or '--gpg [<keyid>]'"
        )

    password, prompt = parse_password_and_prompt_args(args)

    # If `--gpg` was set without argument it has the value `True` and
    # we will try to sign with the default key
    gpg_use_default = args.gpg is True

    # Otherwise we interpret it as actual keyid
    gpg_keyid = None
    if args.gpg is not True:
        gpg_keyid = args.gpg

    # If no_command is specified run in_toto_run without executing a command
    if args.no_command:
        args.link_cmd = []

    elif not args.link_cmd:  # pragma: no branch
        parser.print_usage()
        parser.error(
            "No command specified."
            " Please specify (or use the --no-command option)"
        )

    link = None
    try:
        # We load the key here because it might prompt the user for a password in
        # case the key is encrypted. Something that should not happen in the lib.
        signer = None
        if args.signing_key:
            if prompt:
                password = getpass()

            if password is not None:
                password = password.encode()

            signer = load_crypto_signer_from_pkcs8_file(
                args.signing_key, password
            )

        link = runlib.in_toto_run(
            args.step_name,
            args.materials,
            args.products,
            args.link_cmd,
            record_streams=args.record_streams,
            gpg_keyid=gpg_keyid,
            gpg_use_default=gpg_use_default,
            gpg_home=args.gpg_home,
            exclude_patterns=args.exclude_patterns,
            base_path=args.base_path,
            lstrip_paths=args.lstrip_paths,
            metadata_directory=args.metadata_directory,
            use_dsse=args.use_dsse,
            timeout=args.run_timeout,
            signer=signer,
        )

    except Exception as e:  # noqa: BLE001
        LOG.error("(in-toto-run) %s: %s", type(e).__name__, e)
        sys.exit(1)

    if (
        link
        and getattr(link, "signed", None)
        and link.signed.byproducts.get("return-value")
        and link.signed.byproducts.get("return-value") != 0
    ):
        sys.exit(link.signed.byproducts.get("return-value"))
    sys.exit(0)
