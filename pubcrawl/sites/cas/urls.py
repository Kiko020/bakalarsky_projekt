import re
from urllib.parse import parse_qsl, urlsplit

from ...common.urls import normalize_url


EXCLUDED = re.compile(r"^/(?:tag|vyhladavanie|search|diskusia|diskusie|galeria|galerie|foto|video|autori|rss|horoskopy|kvizy)(?:/|$)", re.I)
LISTING_ROOTS = {"spravy", "celebrity", "sport", "zena", "auto", "recepty", "krimi", "regiony"}


def normalize(url, base="https://www.cas.sk/"):
    return normalize_url(url, base=base, hosts={"cas.sk", "www.cas.sk"},
                         canonical_host="www.cas.sk")


def article_id(url):
    parts = urlsplit(url)
    return parts.path.rstrip("/") or None


def kind(url):
    parts = urlsplit(url)
    path = parts.path.rstrip("/") or "/"
    if EXCLUDED.match(path + "/"):
        return None
    if any(key.lower() in {"diskusia", "gallery", "foto", "video"} for key, _ in parse_qsl(parts.query)):
        return None
    if path == "/robots.txt":
        return "robots"
    if path.endswith((".xml", ".xml.gz")) and "sitemap" in path.lower():
        return "sitemap"
    if path == "/":
        return "listing"
    segments = [segment for segment in path.split("/") if segment]
    if segments and segments[-1].isdigit():
        return "listing"
    if len(segments) == 1 and segments[0].lower() in LISTING_ROOTS:
        return "listing"
    # Cas articles have stable slug paths (usually section/subsection/article-slug).
    return "article" if len(segments) >= 2 else None
