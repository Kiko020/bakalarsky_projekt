import re
from urllib.parse import parse_qsl, urlsplit

from ...common.urls import normalize_url

ARTICLE = re.compile(r"^/cl/\d+/(\d+)(?:/|$)")
EXCLUDED = re.compile(r"(?:^|/)(?:diskusia|diskusie|galeria|galerie|foto|search|vyhladavanie)(?:/|$)", re.I)


def normalize(url, base="https://www.topky.sk/"):
    return normalize_url(url, base=base, hosts={"topky.sk", "www.topky.sk"},
                         canonical_host="www.topky.sk")


def article_id(url):
    match = ARTICLE.match(urlsplit(url).path)
    return match.group(1) if match else None


def kind(url):
    parts = urlsplit(url)
    if EXCLUDED.search(parts.path):
        return None
    if any(k.lower() in {"diskusia", "gallery", "foto"} for k, _ in parse_qsl(parts.query)):
        return None
    if article_id(url):
        return "article"
    if parts.path == "/robots.txt":
        return "robots"
    if parts.path.endswith((".xml", ".xml.gz")) and "sitemap" in parts.path.lower():
        return "sitemap"
    if parts.path == "/" or re.match(r"^/se/\d+(?:/|$)", parts.path):
        return "listing"
    return None
