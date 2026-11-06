#!/usr/bin/env python3
"""Export every SQLite archive in a directory to a separate JSONL file."""

import argparse
from pathlib import Path
import sqlite3
import sys

from export_articles import ExportError, export_articles


DATABASE_SUFFIXES = {".db", ".sqlite", ".sqlite3"}


def parser():
    result = argparse.ArgumentParser(
        description="Export all SQLite article archives in a directory as JSONL files."
    )
    result.add_argument("input_directory", type=Path, help="directory containing SQLite archives")
    result.add_argument("output_directory", type=Path, help="directory for exported JSONL files")
    return result


def export_directory(input_directory, output_directory):
    input_directory = input_directory.expanduser().resolve()
    output_directory = output_directory.expanduser().resolve()
    if not input_directory.is_dir():
        raise ExportError(f"input directory does not exist: {input_directory}")

    databases = sorted(
        path for path in input_directory.iterdir()
        if path.is_file() and path.suffix.lower() in DATABASE_SUFFIXES
    )
    if not databases:
        raise ExportError(f"no SQLite database files found in {input_directory}")

    output_directory.mkdir(parents=True, exist_ok=True)
    failures = 0
    for database_path in databases:
        output_path = output_directory / f"{database_path.stem}.jsonl"
        try:
            with output_path.open("w", encoding="utf-8", newline="\n") as output:
                export_articles(database_path, output)
        except (ExportError, OSError, sqlite3.Error) as exc:
            failures += 1
            print(f"{database_path.name}: {exc}", file=sys.stderr)
            # Avoid leaving a partial export that could be mistaken for a complete one.
            output_path.unlink(missing_ok=True)
        else:
            print(f"Exported {database_path.name} -> {output_path}")
    return 1 if failures else 0


def main(argv=None):
    arguments = parser().parse_args(argv)
    try:
        return export_directory(arguments.input_directory, arguments.output_directory)
    except (ExportError, OSError) as exc:
        print(f"export_directory: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
