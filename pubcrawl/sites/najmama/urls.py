import re
from urllib.parse import parse_qsl, urlsplit

from ...common.urls import normalize_url


ARTICLE = re.compile(r"^/clanok/([A-Za-z0-9]{7})/[^/]+/?$", re.I)
SECTION_ROOTS = {
    "deti", "horoskopy", "lifestyle", "materska-a-rodicovska",
    "premiove-citanie", "tehotenstvo", "tv-najmama", "zdravie",
}
EXCLUDED_ROOTS = {
    "api", "cdn-cgi", "clanok", "diskusia", "error", "foto", "forum",
    "galeria", "katalog", "live", "search", "vyhladavanie",
}
EXCLUDED_QUERY_PARAMETERS = {"comments", "diskusia", "foto", "gallery", "video"}


def normalize(url, base="https://najmama.aktuality.sk/"):
    return normalize_url(
        url,
        base=base,
        hosts={"najmama.aktuality.sk"},
        canonical_host="najmama.aktuality.sk",
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
    if not segments or segments[0] in EXCLUDED_ROOTS:
        return None
    if segments[0] in SECTION_ROOTS and len(segments) <= 2:
        return "listing"
    # Topic index/details and author archives are article discovery pages.
    if segments[0] == "temy" and len(segments) == 1:
        return "listing"
    if segments[0] in {"tema", "autor"} and 2 <= len(segments) <= 3:
        return "listing"
    return None
