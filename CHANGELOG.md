# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-15

### Added
- Initial release of md-hierarchy CLI tool
- Split markdown files into hierarchical folder structures based on heading levels
- Merge folder structures back into single markdown files
- Support for heading levels 1-4 with configurable extraction level
- File naming with numeric prefixes and sanitized titles
- README.md files for parent heading content
- Edge case handling:
  - Empty headings → `Untitled-Section-N`
  - Duplicate headings → Append `-2`, `-3`, etc.
  - Skipped heading levels → Insert `00-Content/` folder
  - Content before first heading → `00-Frontmatter/README.md`
  - Heading attributes preservation
- Command-line options:
  - `--level` / `-l`: Specify heading level to extract (1-4)
  - `--overwrite`: Overwrite existing output directory
  - `--verbose` / `-v`: Print detailed operation log
  - `--dry-run`: Preview operations without writing files
- Round-trip compatibility (split → merge produces equivalent content)
- Preservation of all markdown elements:
  - Code blocks (fenced and indented)
  - Lists (ordered and unordered)
  - Tables
  - Images and links
  - Blockquotes
  - Horizontal rules
- Comprehensive test suite
- Documentation and usage examples

[0.1.0]: https://github.com/ergut/md-hierarchy/releases/tag/v0.1.0
