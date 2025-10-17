"""Command-line interface for md-hierarchy."""

import sys
from pathlib import Path
import click

from .split import split_markdown
from .merge import merge_markdown
from . import __version__


@click.group()
@click.version_option(version=__version__)
def cli():
    """md-hierarchy: Split and merge markdown files based on heading hierarchy.

    \b
    A tool for working with large markdown documents by converting them into
    navigable folder structures and back.

    \b
    Common workflows:
      • Split a long document into sections for easier editing
      • Organize documentation into a folder-based structure
      • Merge edited sections back into a single document
      • Round-trip conversion without losing content

    \b
    Available commands:
      split   Convert markdown file → folder structure
      merge   Convert folder structure → markdown file

    \b
    Quick start:
      $ md-hierarchy split document.md ./output
      $ # Edit files in ./output/...
      $ md-hierarchy merge ./output updated.md

    \b
    For detailed help on a command:
      $ md-hierarchy split --help
      $ md-hierarchy merge --help
    """
    pass


@cli.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.argument('output_dir', type=click.Path(path_type=Path))
@click.option(
    '--level', '-l',
    type=click.IntRange(1, 4),
    default=3,
    help='Heading level to extract as files (1-4, default: 3)'
)
@click.option(
    '--overwrite',
    is_flag=True,
    help='Overwrite output directory if it exists'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Print detailed operation log'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Show what would be done without writing files'
)
def split(input_file, output_dir, level, overwrite, verbose, dry_run):
    """Split a markdown file into hierarchical folder structure.

    Converts a markdown file with headings into a navigable folder hierarchy.
    Each heading level becomes a directory level, with content extracted as
    individual markdown files at your target level.

    INPUT_FILE: Path to the markdown file to split

    OUTPUT_DIR: Directory where the folder structure will be created

    \b
    Examples:
      # Split at H3 level (default) - most common use case
      $ md-hierarchy split proposal.md ./output

      Creates:
        output/01-Introduction/00-__intro__.md
        output/01-Introduction/01-Background/00-__intro__.md
        output/01-Introduction/01-Background/01-Motivation.md
        output/01-Introduction/01-Background/02-Goals.md
        output/02-Methods/00-__intro__.md

      00-__intro__.md files contain heading + intro content (always created).
      H3 sections become individual .md files.

      # Split at H2 level - creates fewer, larger files
      $ md-hierarchy split proposal.md ./output --level 2

      # Test what will happen without creating files
      $ md-hierarchy split proposal.md ./output --dry-run

      # Overwrite existing output directory
      $ md-hierarchy split proposal.md ./output --overwrite
    """
    try:
        result = split_markdown(
            input_file=input_file,
            output_dir=output_dir,
            target_level=level,
            overwrite=overwrite,
            verbose=verbose,
            dry_run=dry_run,
        )

        if dry_run:
            click.echo(f"\n[DRY RUN] Would split {result.sections_count} sections "
                      f"into {result.files_count} files across {result.folders_count} folders")
        else:
            click.echo(f"\nSplit {result.sections_count} sections "
                      f"into {result.files_count} files across {result.folders_count} folders")
            click.echo(f"Output: {output_dir}")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except FileExistsError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('input_dir', type=click.Path(exists=True, path_type=Path))
@click.argument('output_file', type=click.Path(path_type=Path))
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Print detailed operation log'
)
def merge(input_dir, output_file, verbose):
    """Merge hierarchical folder structure into a single markdown file.

    Reconstructs a markdown file from a folder structure created by split.
    Folders are processed in numerical order (01, 02, ...) and converted
    back to their original heading hierarchy.

    INPUT_DIR: Directory containing the split markdown structure

    OUTPUT_FILE: Path where the merged markdown file will be written

    \b
    Examples:
      # Merge split folders back into a single file
      $ md-hierarchy merge ./output merged.md

      Result: All folders and files in ./output are combined into merged.md
      with proper heading levels restored (folder depth = heading level).

      # Merge with detailed progress logging
      $ md-hierarchy merge ./split-docs final.md --verbose

      Shows each file being processed:
        Processing: 01-Introduction/00-__intro__.md
        Processing: 01-Introduction/01-Background/00-__intro__.md
        Processing: 01-Introduction/01-Background/01-Motivation.md
        ...
        Merged 15 files into final.md

      # Perfect round-trip example
      $ md-hierarchy split document.md ./split-output
      $ md-hierarchy merge ./split-output reconstructed.md
      $ diff document.md reconstructed.md  # Should be identical
    """
    try:
        result = merge_markdown(
            input_dir=input_dir,
            output_file=output_file,
            verbose=verbose,
        )

        click.echo(f"\nMerged {result.files_merged} files into {result.output_path}")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except NotADirectoryError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()
