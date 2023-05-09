import sys

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.parsers.rst.directives import unchanged
from docutils.statemachine import StringList

from in_toto import in_toto_run


class ArgparseUsageEpilog(Directive):
    """Sphinx directive to modify argparse epilog to render nicely.

    Expects the function pointed to by ':ref:' to return an ArgumentParser
    instance, with an 'epilog', whose first line is 'EXAMPLE USAGE'. It then
    marks up that line as Sphinx title and iterates over the remaining lines to
    inject code block markup before lines that start with two spaces indentation
    and have a preceding blank line.

    Example of expected 'epilog':

    '''EXAMPLE USAGE

    Lorem ipsum dolor sit amet, consectetur adipisici

      # Execute {prog} with --foo and --baz
      {prog} --foo -- baz

    '''
    NOTE: There should be no indentation before the example descriptions.

    Example usage of directive:

      .. argparse-epilog::
        :ref: in_toto.in_toto_run.create_parser
        :prog: in-toto-run


    """

    has_content = True
    option_spec = dict(ref=unchanged, prog=unchanged)

    def run(self):
        # Parse function in :ref:, e.g. 'in_toto.in_toto_run.create_parser'
        _ref_parts = self.options["ref"].split(".")
        module_name = ".".join(_ref_parts[:-1])
        attr_name = _ref_parts[-1]
        parser_module = __import__(
            module_name, globals(), locals(), [attr_name]
        )
        parser_func = getattr(parser_module, attr_name)

        # Get parser, temporarily patching sys.argv to make argparse expand to the
        # desired program name in the examples using the :prog: option.
        prog = self.options["prog"]
        _argv_backup = sys.argv
        sys.argv = sys.argv = [prog]
        parser = parser_func()
        sys.argv = _argv_backup

        # Parse and mark-up epilog
        epilog_lines = parser.epilog.split("\n")
        assert epilog_lines, "moot '.. argparse-epilog::' with empty 'epilog'"

        # The first line is expected to be the title
        title = epilog_lines.pop(0)
        assert title == "EXAMPLE USAGE", "missing 'epilog' title"
        title_node = nodes.title(text=title.title())

        # Copy remaining lines (body) as they are and ...
        epilog_lines_len = len(epilog_lines)
        epilog_lines_dest = []
        for idx, line in enumerate(epilog_lines):
            epilog_lines_dest.append(line)

            # ... inject ReST markup for code snippets, if the current line is empty
            # and there is a next line, which starts with two spaces.
            if line.strip() == "":
                if epilog_lines_len > idx + 1:
                    next_line = epilog_lines[idx + 1]
                    if next_line.startswith("  "):
                        epilog_lines_dest.append(".. code-block:: sh")
                        epilog_lines_dest.append("")

        # Parse epilog body as ReST
        text_node = nodes.paragraph()
        self.state.nested_parse(StringList(epilog_lines_dest), 0, text_node)

        return [nodes.section("", title_node, text_node, ids=["epilog"])]


def setup(app):
    app.add_directive("argparse-epilog", ArgparseUsageEpilog)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
