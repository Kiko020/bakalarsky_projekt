import json
import scrapy
from .parser import parse_qa, parse_forum, parse_blog, extract_text_from_ast
from .urls import kind, normalize


class ModryKonikSpider(scrapy.Spider):
    name = "modry_konik"
    allowed_domains = ["modrykonik.sk", "www.modrykonik.sk"]

    start_urls = (
        "https://www.modrykonik.sk/ask-an-expert/",
        "https://www.modrykonik.sk/forum/topics/",
        "https://www.modrykonik.sk/blogs/",
    )

    custom_settings = {
        "SCHEDULER": "scrapy.core.scheduler.Scheduler",
        "JOBDIR": "crawls/modry_konik_prod",
        "USER_AGENT": "ModryKonikArchiveBot/0.1",
        "ROBOTSTXT_USER_AGENT": "ModryKonikArchiveBot",
        "DOWNLOAD_DELAY": 3,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 5,
        "AUTOTHROTTLE_MAX_DELAY": 60,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 0.5,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "PLAYWRIGHT_MAX_PAGES_PER_CONTEXT": 2,
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000,
        "FEEDS": {
            "data/modry_konik_prod.jsonl": {
                "format": "jsonlines",
                "encoding": "utf8",
                "overwrite": False,
            }
        },
    }

    def parse(self, response):
        for href in response.css("a::attr(href)").getall():
            url = normalize(href, response.url)
            if not url:
                continue

            k = kind(url)
            if k == "listing":
                if "/forum/category/" in url:
                    yield response.follow(
                        url,
                        callback=self.parse_category_playwright,
                        meta={"playwright": True, "playwright_include_page": True},
                    )
                else:
                    yield response.follow(url, callback=self.parse)
            elif k == "article_expert":
                yield response.follow(url, callback=self.parse_expert)
            elif k == "article_forum":
                yield response.follow(url, callback=self.parse_forum)
            elif k == "article_blog":
                yield response.follow(url, callback=self.parse_blog)

    async def parse_category_playwright(self, response):
        page = response.meta.get("playwright_page")
        if not page:
            return

        try:
            await page.wait_for_selector("a[href*='/forum/']", timeout=20000)
            links = await page.eval_on_selector_all(
                "a[href*='/forum/']",
                "elements => elements.map(el => el.href)",
            )
        except Exception as e:
            self.logger.error(f"Playwright chyba pre {response.url}: {e}")
            return
        finally:
            await page.close()

        seen = set()
        for raw_link in links:
            if any(x in raw_link for x in ("/forum/thread/new/", "/forum/topic/info/", "?page=last", "?scrollto=")):
                continue

            url = normalize(raw_link, response.url)
            if not url or url in seen:
                continue
            seen.add(url)

            k = kind(url)
            if k == "article_forum":
                yield scrapy.Request(url, callback=self.parse_forum)
            elif k == "listing" and "/forum/category/" in url:
                yield scrapy.Request(
                    url,
                    callback=self.parse_category_playwright,
                    meta={"playwright": True, "playwright_include_page": True},
                )

    def parse_expert(self, response):
        try:
            item = parse_qa(response)
        except Exception as exc:
            self.logger.debug("Expert parse skipped %s: %s", response.url, exc)
            return

        yield {
            "messages": [
                {"role": "user", "content": item["question"]},
                {"role": "assistant", "content": item["answer"]},
            ],
            "source_url": response.url,
            "title": item["title"],
            "source": "poradna",
        }

    def parse_forum(self, response):
        try:
            title, pairs = parse_forum(response)
        except Exception as exc:
            self.logger.debug("Forum parse skipped %s: %s", response.url, exc)
            return

        for pair in pairs:
            yield {
                "messages": [
                    {"role": "user", "content": pair["question"]},
                    {"role": "assistant", "content": pair["answer"]},
                ],
                "source_url": response.url,
                "title": title,
                "source": "forum",
                "likes": pair["likes"],
            }

    def parse_blog(self, response):
        try:
            item = parse_blog(response)
        except Exception as exc:
            self.logger.debug("Blog parse skipped %s: %s", response.url, exc)
            return

        api_url = f"https://www.modrykonik.sk/api/blogs/message/{item['post_id']}/comments/"
        yield scrapy.Request(
            api_url,
            callback=self.parse_blog_comments,
            meta={
                "question": item["question"],
                "title": item["title"],
                "source_url": response.url,
            },
        )

    def parse_blog_comments(self, response):
        try:
            data = json.loads(response.text)
            comments = data.get("comments", [])
        except Exception as exc:
            self.logger.debug("Blog API parse skipped %s: %s", response.url, exc)
            return

        question = response.meta["question"]
        title = response.meta["title"]
        source_url = response.meta["source_url"]

        for comment in comments:
            answer_text = extract_text_from_ast(comment.get("textAST"))
            if not answer_text or len(answer_text) < 20:
                continue

            likes = comment.get("likeable", {}).get("likesCount", 0)

            yield {
                "messages": [
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": answer_text},
                ],
                "source_url": source_url,
                "title": title,
                "source": "blog",
                "likes": likes,
            }
