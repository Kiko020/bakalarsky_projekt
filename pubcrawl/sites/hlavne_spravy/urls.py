import re
from urllib.parse import parse_qsl, urlsplit

from ...common.urls import normalize_url


ARTICLE = re.compile(r"/(\d{6,})/?$")
EXCLUDED_ROOTS = {
    "author", "autori", "blog", "diskusia", "feed", "search", "tag",
    "wp-admin", "wp-content", "wp-includes", "wp-json",
}
EXCLUDED_QUERY_PARAMETERS = {"comments", "diskusia", "foto", "gallery", "video"}
PAGINATION_SEGMENTS = {"page"}


def normalize(url, base="https://www.hlavnespravy.sk/"):
    return normalize_url(url, base=base, hosts={"hlavnespravy.sk", "www.hlavnespravy.sk"},
                         canonical_host="www.hlavnespravy.sk")


def article_id(url):
    parts = urlsplit(url)
    segments = [segment for segment in parts.path.split("/") if segment]
    if len(segments) < 2:
        return None
    match = ARTICLE.search(parts.path)
    return match.group(1) if match else None


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
    if segments and segments[0] in EXCLUDED_ROOTS:
        return None
    if article_id(url):
        return "article"
    if path == "/":
        return "listing"
    if "page" in segments and segments[-1].isdigit():
        return "listing"
    if query_keys - {"page", "paged"}:
        return None
    # WordPress category archives use /category/<slug>/ and /page/<n>/.
    return "listing" if segments and segments[0] == "category" else None
