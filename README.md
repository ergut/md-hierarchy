<p align="center">
  <img src="assets/logo-banner.png" alt="md-hierarchy logo" width="600">
</p>

# md-hierarchy

A CLI tool that splits markdown files into hierarchical folder structures based on heading levels, and can reconstruct the original markdown from the split pieces.

## Features

- **Split** markdown files into navigable folder hierarchies
- **Merge** folder structures back into single markdown files
- Preserves all markdown elements (code blocks, lists, tables, links, etc.)
- Handles edge cases (duplicate headings, empty headings, skipped levels)
- Round-trip compatible (split → merge produces equivalent content)
- Dry-run mode to preview operations

## Installation

```bash
# From PyPI
pip install md-hierarchy

# From source
pip install -e .

# With development dependencies
pip install -e ".[dev]"
```

## Usage

### Split Command

Split a markdown file into a hierarchical folder structure:

```bash
md-hierarchy split input.md output_dir --level 3
```

**Options:**

- `--level, -l`: Heading level to extract as files (1-4, default: 3)
- `--overwrite`: Overwrite output directory if it exists
- `--verbose, -v`: Print detailed operation log
- `--dry-run`: Show what would be done without writing files

**Example:**

```bash
# Split at level 3 (H3 headings become files)
md-hierarchy split proposal.md ./output --level 3

# Split with overwrite
md-hierarchy split proposal.md ./output --level 2 --overwrite

# Preview without creating files
md-hierarchy split proposal.md ./output --dry-run
```

### Merge Command

Merge a folder structure back into a single markdown file:

```bash
md-hierarchy merge input_dir output.md
```

**Options:**

- `--verbose, -v`: Print detailed operation log

**Example:**

```bash
# Merge folder structure
md-hierarchy merge ./output merged.md

# Merge with verbose output
md-hierarchy merge ./split-docs final.md --verbose
```

## Output Structure

When splitting at level 3, the tool creates this structure:

```
output-dir/
├── 00-__frontmatter__.md            # Content before first heading (if exists)
├── 01-Introduction/
│   ├── 00-__intro__.md              # H1 heading + intro content (always created)
│   ├── 01-Background/
│   │   ├── 00-__intro__.md          # H2 heading + intro content (always created)
│   │   ├── 01-Problem-Statement.md  # H3 section
│   │   └── 02-Research-Gap.md       # H3 section
│   └── 02-Objectives/
│       ├── 00-__intro__.md          # H2 heading (even if no intro content)
│       └── 01-Primary-Goals.md
└── 02-Methodology/
    └── 00-__intro__.md              # H1 heading + content
```

## File Naming Convention

- **Folders:** `NN-Sanitized-Title/` (e.g., `01-Introduction/`)
- **Intro files:** `00-__intro__.md` (always created for every heading folder)
- **Frontmatter:** `00-__frontmatter__.md` (at root, only if content exists before first heading)
- **Section files:** `NN-Sanitized-Title.md` (e.g., `01-Problem-Statement.md`)
- Numbers are zero-padded (01, 02, ..., 99)
- Special characters (`/ \ : * ? " < > |`) are removed
- Spaces are replaced with hyphens
- Maximum length: 50 characters

### Key Design Decisions

- `00-__intro__.md` is **always created** for every heading folder, even if empty
  - This provides a consistent structure and an easy place to add intro text later
  - Contains the heading declaration and any content before child sections
- The `00-` prefix ensures intro files sort first in directory listings
- The `__intro__` naming (double underscore) clearly marks these as special/meta files
- Frontmatter files are created at the root only when pre-heading content exists

## Edge Cases Handled

1. **Empty headings** → `Untitled-Section-N`
2. **Duplicate titles** → Append `-2`, `-3`, etc.
3. **Skipped levels** (H1 → H3) → Insert `00-Content/` folder
4. **Content before first heading** → `00-__frontmatter__.md` at root
5. **Heading attributes** (e.g., `{#id .class}`) → Preserved in content
6. **Headings with no intro content** → `00-__intro__.md` still created (with just the heading)

## Round-Trip Compatibility

The tool is designed for round-trip operations:

```bash
# Split
md-hierarchy split original.md ./split --level 3

# Merge
md-hierarchy merge ./split reconstructed.md

# Content should be equivalent
diff original.md reconstructed.md
```

## Development

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in development mode
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Run Tests with Coverage

```bash
pytest --cov=md_hierarchy --cov-report=html
```

## Requirements

- Python 3.8+
- Dependencies:
  - `markdown-it-py` - Markdown parsing
  - `click` - CLI framework

## License

MIT
