import re
from urllib.parse import parse_qsl, urlsplit

from ...common.urls import normalize_url


ARTICLE = re.compile(r"(?:^|/)clanok/(\d+)(?:[-/]|$)", re.I)
EXCLUDED_ROOTS = {
    "autor", "bleskove-spravy", "info", "kategoria", "mreporter",
    "podcasty", "trendove-temy", "tv", "vyhladavanie",
}
LISTING_ROOTS = {
    "ahojmama", "auto", "cestovanie", "ekonomika", "koktail", "kultura",
    "nazory", "sportweb", "spravy", "uzitocna", "vat", "vino", "zahrada",
    "zdravie", "zena",
}
EXCLUDED_QUERY_PARAMETERS = {"diskusia", "foto", "gallery", "video"}


def normalize(url, base="https://www.pravda.sk/"):
    return normalize_url(
        url,
        base=base,
        hosts={"pravda.sk", "www.pravda.sk"},
        canonical_host="www.pravda.sk",
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
    if path.endswith((".xml", ".xml.gz")) and "sitemap" in path.lower():
        return "sitemap"
    if path == "/":
        return "listing"
    segments = [segment.lower() for segment in path.split("/") if segment]
    if not segments or segments[0] in EXCLUDED_ROOTS:
        return None
    return "listing" if segments[0] in LISTING_ROOTS else None
