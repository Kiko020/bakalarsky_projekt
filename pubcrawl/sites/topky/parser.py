"""Topky.sk adapter over the shared metadata-first article parser."""

from ...common.parser import parse_article as _parse_article
from .urls import article_id, normalize


def parse_article(response):
    return _parse_article(
        response,
        normalize_url=normalize,
        article_identifier=article_id,
    )
