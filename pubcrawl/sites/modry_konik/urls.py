import re
from urllib.parse import urlsplit
from ...common.urls import normalize_url

ARTICLE_EXPERT = re.compile(r"^/ask-an-expert/[^/]+/[^/]+/?$", re.I)
ARTICLE_FORUM = re.compile(r"^/forum/[^/]+/[^/]+/?$", re.I)
ARTICLE_BLOG = re.compile(r"^/blogs/[^/]+/(message|article)/[^/]+/?$", re.I)


def normalize(url, base="https://www.modrykonik.sk/"):
    return normalize_url(url, base=base, hosts={"www.modrykonik.sk", "modrykonik.sk"},
                         canonical_host="www.modrykonik.sk")


def article_id(url):
    path = urlsplit(url).path
    m = ARTICLE_EXPERT.match(path) or ARTICLE_FORUM.match(path) or ARTICLE_BLOG.match(path)
    return m.group(0) if m else None


def kind(url):
    parts = urlsplit(url)
    path = parts.path.rstrip("/") or "/"
    segments = [s.lower() for s in path.split("/") if s]

    if path == "/robots.txt":
        return "robots"
    if path.endswith((".xml", ".xml.gz")) and "sitemap" in path.lower():
        return "sitemap"
    if not segments:
        return None

    if segments[0] == "ask-an-expert":
        if len(segments) == 1:
            return "listing"
        if len(segments) == 2:
            return "listing"
        if len(segments) == 3:
            return "article_expert"
        return None

    if segments[0] == "forum":
        if len(segments) >= 3 and segments[1] not in {"category", "topics"}:
            return "article_forum"
        
        if len(segments) <= 2 or segments[1] in {"category", "topics"}:
            return "listing"
            
        return None

    if segments[0] == "blogs":
        if len(segments) == 1:
            return "listing"
        if len(segments) == 2:
            return "listing"
        if len(segments) >= 4 and segments[2] in {"message", "article"}:
            return "article_blog"
        return None

    return None