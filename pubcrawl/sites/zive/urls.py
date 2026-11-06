import re
from urllib.parse import parse_qsl, urlsplit

from ...common.urls import normalize_url


ARTICLE = re.compile(r"^/clanok/([A-Za-z0-9]{7})/[^/]+/?$", re.I)
LISTING_ROOTS = {
    "ai", "bezpecnost", "forum", "herna-zona", "hoaxy", "mobilmania",
    "podcasty", "premium", "recenzie", "setrenie-energiami", "spravy",
    "tipy-a-triky", "tv-a-operatori", "veda", "video",
}
EXCLUDED_ROOTS = {
    "api", "autor", "cdn-cgi", "clanok", "diskusia", "error", "foto",
    "galeria", "live", "podcast", "search", "tag", "vyhladavanie",
}
EXCLUDED_QUERY_PARAMETERS = {"comments", "diskusia", "foto", "gallery", "video"}


def normalize(url, base="https://zive.aktuality.sk/"):
    return normalize_url(
        url,
        base=base,
        hosts={"zive.aktuality.sk"},
        canonical_host="zive.aktuality.sk",
    )


def article_id(url):
    match = ARTICLE.match(urlsplit(url).path)
    return match.group(1) if match else None


def kind(url):
    parts = urlsplit(url)
    path = parts.path.rstrip("/") or "/"
    segments = [segment.lower() for segment in path.split("/") if segment]
    query_keys = {key.lower() for key, _ in parse_qsl(parts.query)}
    if query_keys & EXCLUDED_QUERY_PARAMETERS:
        return None
    if article_id(url):
        return "article"
    if path == "/robots.txt":
        return "robots"
    if path.endswith((".xml", ".xml.gz")) and "sitemap" in path.lower():
        return "sitemap"
    if query_keys - {"page", "strana"}:
        return None
    if path == "/":
        return "listing"
    if segments and segments[0] not in EXCLUDED_ROOTS:
        if segments[0] in LISTING_ROOTS and len(segments) <= 2:
            return "listing"
    return None
