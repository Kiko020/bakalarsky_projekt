BOT_NAME = "pubcrawl"
SPIDER_MODULES = [
    "pubcrawl.sites.topky.spider",
    "pubcrawl.sites.cas.spider",
    "pubcrawl.sites.pravda.spider",
    "pubcrawl.sites.pravda_blog.spider",
    "pubcrawl.sites.dennikn_blog.spider",
    "pubcrawl.sites.hnonline.spider",
    "pubcrawl.sites.sport_aktuality.spider",
    "pubcrawl.sites.koktejl.spider",
    "pubcrawl.sites.pluska.spider",
    "pubcrawl.sites.zive.spider",
    "pubcrawl.sites.diva.spider",
    "pubcrawl.sites.najmama.spider",
    "pubcrawl.sites.sita.spider",
    "pubcrawl.sites.teraz.spider",
    "pubcrawl.sites.hlavne_spravy.spider",
    "pubcrawl.sites.bratislavske_noviny.spider",
    "pubcrawl.sites.modry_konik.spider",
]
SCHEDULER = "pubcrawl.common.scheduler.SQLiteScheduler"
ROBOTSTXT_OBEY = True
# Override this with a descriptive contact URL before crawling a production site.
USER_AGENT = "PubCrawlBot/0.2"
ROBOTSTXT_USER_AGENT = "PubCrawlBot"
CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 2
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1
RETRY_TIMES = 3
DOWNLOAD_TIMEOUT = 30
DOWNLOAD_MAXSIZE = 20 * 1024 * 1024
COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False
REMOTE_CONTROL_ENABLED = False
LOG_LEVEL = "INFO"
HTTPERROR_ALLOW_ALL = True
