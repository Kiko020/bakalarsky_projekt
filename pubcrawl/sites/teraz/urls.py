import re
from urllib.parse import parse_qsl, urlsplit

from ...common.urls import normalize_url


ARTICLE = re.compile(r"/(\d+)-clanok\.html$", re.I)
LISTING_ROOTS = {
    "archiv", "ekonomika", "kaleidoskop", "knihy", "krimi", "kultura",
    "magazin", "najnovsie", "pocasie", "publicistika", "regiony", "slovensko",
    "sport", "svet", "veda", "zahranicie", "zdravie",
}
EXCLUDED_ROOTS = {
    "rss", "odber-xml", "podmienky-pouzivania-xml-odber", "search", "vyhladavanie",
    "diskusia", "galeria", "foto", "video", "wp-admin", "wp-content", "wp-json",
}
EXCLUDED_QUERY_PARAMETERS = {"comments", "diskusia", "gallery", "foto", "video"}


def normalize(url, base="https://www.teraz.sk/"):
    return normalize_url(url, base=base, hosts={"teraz.sk", "www.teraz.sk"},
                         canonical_host="www.teraz.sk")


def article_id(url):
    match = ARTICLE.search(urlsplit(url).path)
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
    if path.lower().endswith(".rss"):
        return "feed"
    if path == "/":
        return "listing"
    if not segments or segments[0] in EXCLUDED_ROOTS:
        return None
    # Teraz section archives paginate with ?p=<offset>.
    if query_keys - {"p"}:
        return None
    return "listing" if segments[0] in LISTING_ROOTS else None
