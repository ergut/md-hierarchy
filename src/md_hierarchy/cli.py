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

    Split a markdown file into a hierarchical folder structure based on headings,
    or merge a folder structure back into a single markdown file.
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

    Extracts sections at the specified heading level as individual files,
    creating a navigable folder hierarchy based on the document structure.

    Examples:

        md-hierarchy split proposal.md ./output

        md-hierarchy split proposal.md ./output --level 2

        md-hierarchy split proposal.md ./output --level 3 --overwrite
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

    Reconstructs a markdown file from a folder structure created by the split
    command, following the numbered naming convention to maintain proper order.

    Examples:

        md-hierarchy merge ./output merged.md

        md-hierarchy merge ./split-docs final.md --verbose
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
