## Introduction

The optional argument `exclude_patterns` in the `in_toto_run` API, also used by `--exclude` in the ```in-toto-run``` command line tool, applies [pathspec](http://python-path-specification.readthedocs.io) to compile [gitignore-style patterns](https://git-scm.com/docs/gitignore). Artifacts (materials and products) matched by an exclude pattern are not recorded when generating link metadata. If a pattern matches a directory, all files and subdirectories are also excluded.

## Pattern Formats
  - A literal hash serves as a comment. Escape the hash with a back-slash to match a literal hash (i.e., `\#`). 
  - A exclamation mark negates the rest of the pattern. Artifacts matched by the rest of the pattern will be the only ones recorded, and everything else will be excluded. Escape the exclamation mark with a back-slash to match a literal exclamation mark (i.e., `\!`).
  - The slash is a directory seperator. Separators at beginning or middle (or both) of a pattern are relative to directory level of particular .gitignore file. Separators at the end of the pattern only  match directories. (e.g., `doc/frotz/` matches `doc/frotz` directory but not `a/doc/frotz` directory; however `frotz/` matches `frotz` and `a/frotz`).
  - A single `/` does not match any file.
  - Leading double asterisks match any proceeding path segments (e.g., `**/foo` matches file or directory `foo` and `**/foo/bar` matches file or directory `bar` anywhere that is directly under directory `foo`).
  - Trailing double asterisks matches any preceeding path segments (e.g., `abc/**` matches all files inside directory `abc`). 
  - A slash followed by two consecutive asterisks and a slash matches path segments between two directories (e.g., `a/**/b` matches `a/b`, `a/x/b`, `a/x/y/b` and so on). 
  - Single asterisks match everything except a slash. 
  - Question marks match any one character except a slash.
  
  More information about pattern formats found in [`gitignore`](https://git-scm.com/docs/gitignore). 

## Special Cases
### Pattern beginning with a slash
  - Match paths directly on the root directory instead of descendant paths. Escape the relative root conversion with an forward slash to match absolute paths. (i.e., 
 `//<pattern>`). 

### Patterns without a beginning slash
  - A single pattern without a beginning slash will match any descendant path, equivalent to `**/<pattern>"`. This also holds for a single pattern with a trailing slash (e.g. `dir/`). 
  - A pattern without a beginning slash but contains at least one prepended directory (e.g. `dir/<pattern>`) should not match `**/dir/<pattern>`. 

### Patterns ending with a slash 
  - A pattern ending with a slash will match all descendant paths if it is a directory level but not if it is a regular file. This is equivalent to `{pattern}/**`.

## Documentation

- [`pathspec`](http://python-path-specification.readthedocs.io/)
- [`gitignore`](https://git-scm.com/docs/gitignore)
