import scrapy
from .parser import parse_qa, parse_forum
from .urls import kind, normalize


class ModryKonikSpider(scrapy.Spider):
    name = "modry_konik"
    allowed_domains = ["modrykonik.sk", "www.modrykonik.sk"]
    start_urls = (
        "https://www.modrykonik.sk/ask-an-expert/",
        "https://www.modrykonik.sk/forum/",
    )

    custom_settings = {
        "SCHEDULER": "scrapy.core.scheduler.Scheduler",
        "USER_AGENT": "ModryKonikArchiveBot/0.1",
        "ROBOTSTXT_USER_AGENT": "ModryKonikArchiveBot",
        "DOWNLOAD_DELAY": 3,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 5,
        "AUTOTHROTTLE_MAX_DELAY": 60,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 0.5,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "FEEDS": {"data/modry_konik.jsonl": {"format": "jsonlines", "encoding": "utf8"}},
    }

    def parse(self, response):
        for href in response.css("a::attr(href)").getall():
            url = normalize(href, response.url)
            if not url:
                continue
            k = kind(url)
            if k == "listing":
                yield response.follow(url, callback=self.parse)
            elif k == "article_expert":
                yield response.follow(url, callback=self.parse_expert)
            elif k == "article_forum":
                yield response.follow(url, callback=self.parse_forum)

    def parse_expert(self, response):
        try:
            item = parse_qa(response)
        except Exception as exc:
            self.logger.error("Expert parse failed %s: %s", response.url, exc)
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
            self.logger.error("Forum parse failed %s: %s", response.url, exc)
            return
        for question, answer in pairs:
            yield {
                "messages": [
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": answer},
                ],
                "source_url": response.url,
                "title": title,
                "source": "forum",
            }