import re
from urllib.parse import parse_qsl, urlsplit

from ...common.urls import normalize_url


ARTICLE = re.compile(r"^/clanok/([A-Za-z0-9]{7})/[^/]+/?$")
LISTING_ROOTS = {
    "celebrity", "europska-tvorba", "horoskopy", "krimi", "kvizy",
    "lifestyle", "offrecord", "slovensko", "sport", "videa",
    "zahranicie", "zaujimavosti",
}
EXCLUDED_QUERY_PARAMETERS = {"comments", "diskusia", "foto", "gallery", "video"}


def normalize(url, base="https://koktejl.azet.sk/"):
    return normalize_url(
        url,
        base=base,
        hosts={"koktejl.azet.sk"},
        canonical_host="koktejl.azet.sk",
    )


def article_id(url):
    match = ARTICLE.match(urlsplit(url).path)
    return match.group(1) if match else None


def kind(url):
    parts = urlsplit(url)
    path = parts.path.rstrip("/") or "/"
    query_keys = {key.lower() for key, _ in parse_qsl(parts.query)}
    if query_keys & EXCLUDED_QUERY_PARAMETERS:
        return None
    if article_id(url):
        return "article"
    if path == "/robots.txt":
        return "robots"
    if path.endswith((".xml", ".xml.gz")) and "sitemap" in path.lower():
        return "sitemap"
    if query_keys - {"page"}:
        return None
    if path == "/":
        return "listing"
    segments = [segment.lower() for segment in path.split("/") if segment]
    if 1 <= len(segments) <= 2 and segments[0] in LISTING_ROOTS:
        return "listing"
    return None
