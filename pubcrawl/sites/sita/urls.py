import re
from urllib.parse import parse_qsl, urlsplit

from ...common.urls import normalize_url


EXCLUDED_ROOTS = {
    "author", "autor", "category", "tag", "feed", "wp-admin", "wp-content",
    "wp-includes", "wp-json", "search", "vyhladavanie", "odber", "diskusia",
    "galeria", "foto", "video", "page",
}
LISTING_ROOTS = {
    "spravy", "slovensko", "svet", "sport", "vofinanciach", "zdravotnictvo",
    "doprava", "skolstvo", "kultura", "regiony", "ekonomika", "technologie",
}
EXCLUDED_QUERY_PARAMETERS = {"amp", "comments", "diskusia", "gallery", "foto", "video"}


def normalize(url, base="https://sita.sk/"):
    return normalize_url(url, base=base, hosts={"sita.sk", "www.sita.sk"},
                         canonical_host="sita.sk")


def article_id(url):
    path = urlsplit(url).path.rstrip("/")
    return path if path and kind(url) == "article" else None


def kind(url):
    parts = urlsplit(url)
    path = parts.path.rstrip("/") or "/"
    segments = [segment.lower() for segment in path.split("/") if segment]
    query_keys = {key.lower() for key, _ in parse_qsl(parts.query)}
    if query_keys & EXCLUDED_QUERY_PARAMETERS:
        return None
    if path == "/robots.txt":
        return "robots"
    if path.endswith((".xml", ".xml.gz")) and "sitemap" in path.lower():
        return "sitemap"
    if path == "/feed" or path.endswith("/feed"):
        return "feed"
    if path == "/":
        return "listing"
    if re.fullmatch(r"/?page/\d+", path):
        return "listing"
    if not segments or segments[0] in EXCLUDED_ROOTS:
        return None
    if len(segments) == 1 and segments[0] in LISTING_ROOTS:
        return "listing"
    # SITA articles use section/slug paths and do not include a numeric ID.
    return "article" if len(segments) >= 2 else None
