import re
from urllib.parse import parse_qsl, urlsplit

from ...common.urls import normalize_url


ARTICLE = re.compile(r"(?:^|/)clanok/[^/]*-(\d{19})/?$", re.I)
EXCLUDED_ROOTS = {
    "article-preview", "docs", "fans-arena", "page", "podcasty", "rss",
    "sport-tv-program", "video", "vysledky",
}
LISTING_ROOTS = {"autor", "najnovsie-spravy", "tema"}
EXCLUDED_QUERY_PARAMETERS = {"comments", "diskusia", "gallery", "foto", "video"}


def normalize(url, base="https://sport.aktuality.sk/"):
    return normalize_url(
        url,
        base=base,
        hosts={"sport.aktuality.sk"},
        canonical_host="sport.aktuality.sk",
    )


def article_id(url):
    match = ARTICLE.search(urlsplit(url).path)
    return match.group(1) if match else None


def kind(url):
    parts = urlsplit(url)
    path = parts.path.rstrip("/") or "/"
    if any(key.lower() in EXCLUDED_QUERY_PARAMETERS for key, _ in parse_qsl(parts.query)):
        return None
    if article_id(url):
        return "article"
    if path == "/robots.txt":
        return "robots"
    if path.endswith((".xml", ".xml.gz")) and "sitemap" in path.lower():
        return "sitemap"
    if path == "/":
        return "listing"
    segments = [segment.lower() for segment in path.split("/") if segment]
    if not segments or segments[0] in EXCLUDED_ROOTS:
        return None
    # Sport sections use flat paths such as /hokej-nhl. Author and topic
    # archives are two-segment paginated listings.
    if len(segments) == 1 or (len(segments) == 2 and segments[0] in LISTING_ROOTS):
        return "listing"
    return None
