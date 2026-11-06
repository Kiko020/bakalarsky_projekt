"""Koktejl.sk adapter over the shared metadata-first article parser."""
import json

from ...common.parser import (
    clean,
    normalized_text,
    parse_article as _parse_article,
    text_blocks,
    walk_json,
)
from .urls import article_id, normalize


def _structured_data(response):
    for raw in response.css('script[type="application/ld+json"]::text').getall():
        try:
            yield from walk_json(json.loads(raw))
        except (TypeError, ValueError):
            continue


def _has_type(node, expected):
    value = node.get("@type")
    return expected in (value if isinstance(value, list) else [value])


def _intro_and_section(response):
    intro = ""
    section = ""
    for node in _structured_data(response):
        if not intro and _has_type(node, "NewsArticle"):
            intro = clean(node.get("description"))
        if not section and _has_type(node, "BreadcrumbList"):
            entries = node.get("itemListElement")
            entries = entries if isinstance(entries, list) else []
            names = [clean(entry.get("name")) for entry in entries if isinstance(entry, dict)]
            section = next((name for name in reversed(names) if name and name.lower() != "domov"), "")
    if not intro:
        heading = response.css("h1")
        candidate = heading[0].xpath("following::p[1]") if heading else []
        intro = clean(candidate[0].xpath("string(.)").get()) if candidate else ""
    return intro, section


def _body_text(response, intro):
    articles = response.css("article")
    if not articles:
        raise ValueError("Article requires a Koktejl.sk article body")
    body = text_blocks(articles[0])
    if not body:
        raise ValueError("Article requires a nonempty Koktejl.sk article body")
    if intro and not normalized_text(body).startswith(normalized_text(intro)):
        body = f"{intro}\n\n{body}"
    return body


def parse_article(response):
    intro, section = _intro_and_section(response)
    item = _parse_article(
        response,
        normalize_url=normalize,
        article_identifier=article_id,
        body_extractor=lambda current: _body_text(current, intro),
    )
    item["intro"] = intro or None
    if section:
        item["section"] = section
    return item
