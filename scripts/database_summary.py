#!/usr/bin/env python3
"""Summarize downloaded articles and crawl queue URL kinds per SQLite archive."""

import argparse
from pathlib import Path
import sqlite3
import sys
from urllib.parse import quote


DATABASE_SUFFIXES = {".db", ".sqlite", ".sqlite3"}


def read_summary(path):
    uri = "file:" + quote(str(path.resolve()), safe="/") + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as database:
        article_count = database.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        queue_counts = database.execute(
            "SELECT kind, COUNT(*) FROM crawl_queue GROUP BY kind ORDER BY kind"
        ).fetchall()
    return article_count, queue_counts


def parser():
    result = argparse.ArgumentParser(
        description="Report article and crawl queue URL-kind counts for SQLite archives."
    )
    result.add_argument("input_directory", type=Path, help="directory containing SQLite archives")
    return result


def main(argv=None):
    arguments = parser().parse_args(argv)
    input_directory = arguments.input_directory.expanduser().resolve()
    if not input_directory.is_dir():
        print(f"database_summary: input directory does not exist: {input_directory}", file=sys.stderr)
        return 1

    databases = sorted(
        path for path in input_directory.iterdir()
        if path.is_file() and path.suffix.lower() in DATABASE_SUFFIXES
    )
    if not databases:
        print(f"database_summary: no SQLite database files found in {input_directory}", file=sys.stderr)
        return 1

    failures = 0
    for path in databases:
        try:
            article_count, queue_counts = read_summary(path)
        except sqlite3.Error as exc:
            failures += 1
            print(f"{path.name}: {exc}", file=sys.stderr)
            continue

        print(f"{path.name}: {article_count} downloaded articles")
        print("  Crawl queue URLs by kind:")
        if queue_counts:
            for kind, count in queue_counts:
                print(f"    {kind}: {count}")
        else:
            print("    (empty)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
