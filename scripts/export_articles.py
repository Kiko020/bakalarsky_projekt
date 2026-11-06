#!/usr/bin/env python3
"""Export parsed archive articles as newline-delimited JSON."""

import argparse
import json
from pathlib import Path
import sqlite3
import sys
from urllib.parse import quote


ARTICLE_COLUMNS = {
    "id",
    "site_article_id",
    "final_url",
    "title",
    "intro",
    "body_text",
    "authors_json",
    "source",
    "published_at",
    "modified_at",
    "section",
    "tags_json",
    "language",
    "images_json",
    "metadata_json",
}

QUERY = """
SELECT site_article_id, final_url, body_text, title, intro, authors_json,
       source, published_at, modified_at, section, tags_json, language,
       images_json, metadata_json
FROM articles
ORDER BY id
"""


class ExportError(Exception):
    """An archive cannot be exported using the expected data contract."""


def _decoded(row, column):
    try:
        return json.loads(row[column])
    except (TypeError, json.JSONDecodeError) as exc:
        raise ExportError(
            f"article {row['site_article_id']!r} has invalid JSON in {column}: {exc}"
        ) from exc


def article_document(row):
    """Convert an articles row to the public JSONL document shape."""
    return {
        "id": row["site_article_id"],
        "url": row["final_url"],
        "text": row["body_text"],
        "meta": {
            "title": row["title"],
            "intro": row["intro"],
            "authors": _decoded(row, "authors_json"),
            "source": row["source"],
            "published_at": row["published_at"],
            "modified_at": row["modified_at"],
            "section": row["section"],
            "tags": _decoded(row, "tags_json"),
            "language": row["language"],
            "images": _decoded(row, "images_json"),
            "metadata": _decoded(row, "metadata_json"),
        },
    }


def open_database(path):
    path = Path(path).expanduser()
    if not path.is_file():
        raise ExportError(f"database does not exist: {path}")

    database_uri = "file:" + quote(str(path.resolve()), safe="/") + "?mode=ro"
    database = sqlite3.connect(database_uri, uri=True)
    database.row_factory = sqlite3.Row

    version = database.execute("PRAGMA user_version").fetchone()[0]
    if version != 2:
        database.close()
        raise ExportError(f"unsupported database schema version {version}; expected version 2")

    columns = {row[1] for row in database.execute("PRAGMA table_info(articles)")}
    missing = sorted(ARTICLE_COLUMNS - columns)
    if missing:
        database.close()
        raise ExportError("articles table is missing columns: " + ", ".join(missing))
    return database


def export_articles(database_path, output):
    """Stream all parsed articles from database_path to a text output."""
    database = open_database(database_path)
    try:
        for row in database.execute(QUERY):
            document = article_document(row)
            output.write(json.dumps(document, ensure_ascii=False, separators=(",", ":")))
            output.write("\n")
    finally:
        database.close()


def parser():
    result = argparse.ArgumentParser(
        description="Export parsed SQLite archive articles as JSONL."
    )
    result.add_argument("database", help="path to a schema-v2 archive database")
    result.add_argument(
        "-o",
        "--output",
        help="output file to replace (default: standard output)",
    )
    return result


def main(argv=None):
    arguments = parser().parse_args(argv)
    output = sys.stdout
    close_output = False
    try:
        if arguments.output:
            database_path = Path(arguments.database).expanduser().resolve()
            output_path = Path(arguments.output).expanduser().resolve()
            if database_path == output_path:
                raise ExportError("output file must not be the input database")
            output = output_path.open("w", encoding="utf-8", newline="\n")
            close_output = True
        export_articles(arguments.database, output)
    except (ExportError, OSError, sqlite3.Error) as exc:
        print(f"export_articles: {exc}", file=sys.stderr)
        return 1
    finally:
        if close_output:
            output.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
