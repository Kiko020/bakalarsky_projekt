# Slovak news article archives

A Scrapy archive crawler for `www.topky.sk`, `www.cas.sk`, `www.pravda.sk`, the `*.blog.pravda.sk` blog network, public blogs on `dennikn.sk`, `hnonline.sk`, `sport.aktuality.sk`, `koktejl.azet.sk`, `www1.pluska.sk`, `zive.aktuality.sk`, `diva.aktuality.sk`, `najmama.aktuality.sk`, `sita.sk`, `www.teraz.sk`, and `www.hlavnespravy.sk`, with parsed articles, metadata, gzip-compressed HTML, duplicate detection, and a crash-resumable SQLite queue. Python 3.11+ and Linux/macOS are supported (the database lock uses `fcntl`). Each site uses the same schema in its own SQLite file.

Shared crawling, parsing, scheduling, storage, and URL-normalization code lives in
`pubcrawl/common`. Each publisher's spider, URL rules, and parsing adaptations live
together under `pubcrawl/sites/<site>`.

Bratislavské noviny (`www.bratislavskenoviny.sk`) is also supported:

```bash
.venv/bin/scrapy crawl bratislavske_noviny -a db=data/bratislavske-noviny-v2.sqlite3 -a run_label=initial-archive
```

Its separate default database is `data/bratislavske-noviny-v2.sqlite3`, using schema
version 2 and the same resume, refresh, and retry controls as the other publishers.
Discovery follows the homepage, editorial sections, district listings, and
`/strana-N` pagination, plus any robots-advertised sitemaps. Numeric article IDs
are taken from the final URL segment. The currently advertised RSS endpoint and
`/sitemap.xml` return 404 and are not seeded. Current robots rules disallow URLs
containing `strana`, including pagination and some article slugs; those requests
remain blocked, limiting archive coverage. Publication labels “Dnes” and “Včera”
are resolved using the response's HTTP Date in `Europe/Bratislava`; unresolved
dates remain null and their visible text is retained in raw metadata.

For a bounded check using a separate database:

```bash
.venv/bin/scrapy crawl bratislavske_noviny -a db=data/bratislavske-noviny-smoke.sqlite3 -s CLOSESPIDER_PAGECOUNT=20 -s CLOSESPIDER_TIMEOUT=120
```

## Install and run

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/scrapy crawl topky -a db=data/topky-v2.sqlite3 -a run_label=initial-archive
```

Archive Cas.sk into its separate default database:

```bash
.venv/bin/scrapy crawl cas -a db=data/cas-v2.sqlite3 -a run_label=initial-archive
```

Archive Pravda.sk into its separate default database:

```bash
.venv/bin/scrapy crawl pravda -a db=data/pravda-v2.sqlite3 -a run_label=initial-archive
```

Archive all public Pravda blogs, including commercial blogs, into their own database:

```bash
.venv/bin/scrapy crawl pravda_blog -a db=data/pravda-blog-v2.sqlite3 -a run_label=initial-archive
```

Archive public Denník N blog posts into a separate database:

```bash
.venv/bin/scrapy crawl dennikn_blog -a db=data/dennikn-blog-v2.sqlite3 -a run_label=initial-archive
```

Archive HN Online into its separate default database:

```bash
.venv/bin/scrapy crawl hnonline -a db=data/hnonline-v2.sqlite3 -a run_label=initial-archive
```

Archive Sport.sk into its separate default database:

```bash
.venv/bin/scrapy crawl sport_aktuality -a db=data/sport-aktuality-v2.sqlite3 -a run_label=initial-archive
```

Archive Koktejl.sk into its separate default database:

```bash
.venv/bin/scrapy crawl koktejl -a db=data/koktejl-v2.sqlite3 -a run_label=initial-archive
```

Archive Pluska.sk into its separate default database:

```bash
.venv/bin/scrapy crawl pluska -a db=data/pluska-v2.sqlite3 -a run_label=initial-archive
```

Archive Živé.sk into its separate default database:

```bash
.venv/bin/scrapy crawl zive -a db=data/zive-v2.sqlite3 -a run_label=initial-archive
```

Archive Diva.sk into its separate default database:

```bash
.venv/bin/scrapy crawl diva -a db=data/diva-v2.sqlite3 -a run_label=initial-archive
```

Archive Najmama.sk into its separate default database:

```bash
.venv/bin/scrapy crawl najmama -a db=data/najmama-v2.sqlite3 -a run_label=initial-archive
```

Archive SITA.sk into its separate default database:

```bash
.venv/bin/scrapy crawl sita -a db=data/sita-v2.sqlite3 -a run_label=initial-archive
```

Archive Teraz.sk into its separate default database:

```bash
.venv/bin/scrapy crawl teraz -a db=data/teraz-v2.sqlite3 -a run_label=initial-archive
```

Archive Hlavné správy into its separate default database:

```bash
.venv/bin/scrapy crawl hlavne_spravy -a db=data/hlavne-spravy-v2.sqlite3 -a run_label=initial-archive
```

Refresh discovery pages or retry failed requests with the same controls as the other spiders:

```bash
.venv/bin/scrapy crawl hnonline -a db=data/hnonline-v2.sqlite3 -a refresh_discovery=true
.venv/bin/scrapy crawl hnonline -a db=data/hnonline-v2.sqlite3 -a retry_failed=true
```

Run commands from this directory. The database and parent directory are created automatically. The existing workspace virtual environment already contains Scrapy 2.19.

The spiders must never share a database: `topky` defaults to `data/topky-v2.sqlite3`, `cas` defaults to `data/cas-v2.sqlite3`, `pravda` defaults to `data/pravda-v2.sqlite3`, `pravda_blog` defaults to `data/pravda-blog-v2.sqlite3`, `dennikn_blog` defaults to `data/dennikn-blog-v2.sqlite3`, `hnonline` defaults to `data/hnonline-v2.sqlite3`, `sport_aktuality` defaults to `data/sport-aktuality-v2.sqlite3`, `koktejl` defaults to `data/koktejl-v2.sqlite3`, `pluska` defaults to `data/pluska-v2.sqlite3`, `zive` defaults to `data/zive-v2.sqlite3`, `diva` defaults to `data/diva-v2.sqlite3`, `najmama` defaults to `data/najmama-v2.sqlite3`, `sita` defaults to `data/sita-v2.sqlite3`, `teraz` defaults to `data/teraz-v2.sqlite3`, and `hlavne_spravy` defaults to `data/hlavne-spravy-v2.sqlite3`. All use schema version 2.

Export every SQLite database in a directory to a matching JSONL file:

```bash
.venv/bin/python scripts/export_directory.py data exports
```

The script processes `.db`, `.sqlite`, and `.sqlite3` files. Each database is exported independently; it continues after a bad database and exits with a nonzero status if any export fails.

Summarize downloaded article totals and queued URL counts by kind for all databases in a directory:

```bash
.venv/bin/python scripts/database_summary.py data
```

Press Ctrl-C once to stop gracefully. Run **the same command** to resume. After a crash, forced termination, or restart, in-flight requests return to the queue automatically. Keep the SQLite database, including its `-wal` and `-shm` files when present; do not copy only the main database while a crawl is running. Use SQLite's backup API for online backups. Do not set `JOBDIR`: this project uses its own persistent scheduler.

Completed articles are never refreshed: the first successfully saved version is retained. A normal restart only finishes existing work. After completion, discover new articles by revisiting listings and sitemaps:

```bash
.venv/bin/scrapy crawl topky -a db=data/topky-v2.sqlite3 -a refresh_discovery=true
```

Retry terminal HTTP, network, or parsing failures explicitly, for example after fixing selectors:

```bash
.venv/bin/scrapy crawl topky -a db=data/topky-v2.sqlite3 -a retry_failed=true
```

The flags can be combined. Robots-blocked URLs remain blocked. Only one crawler process may use a database at a time. A leftover `.lock` file is harmless; the operating system releases the actual lock when a process exits. This release uses schema version 2 and requires a new database; version-1 archives are intentionally not migrated.

For a bounded initial check, use a separate database:

```bash
.venv/bin/scrapy crawl topky -a db=data/smoke.sqlite3 -s CLOSESPIDER_PAGECOUNT=20 -s CLOSESPIDER_TIMEOUT=120
```

For Cas.sk, use a separate bounded database in the same way:

```bash
.venv/bin/scrapy crawl cas -a db=data/cas-smoke.sqlite3 -s CLOSESPIDER_PAGECOUNT=20 -s CLOSESPIDER_TIMEOUT=120
```

For Pravda.sk:

```bash
.venv/bin/scrapy crawl pravda -a db=data/pravda-smoke.sqlite3 -s CLOSESPIDER_PAGECOUNT=20 -s CLOSESPIDER_TIMEOUT=120
```

For the Pravda blog network:

```bash
.venv/bin/scrapy crawl pravda_blog -a db=data/pravda-blog-smoke.sqlite3 -s CLOSESPIDER_PAGECOUNT=20 -s CLOSESPIDER_TIMEOUT=120
```

For HN Online:

```bash
.venv/bin/scrapy crawl hnonline -a db=data/hnonline-smoke.sqlite3 -s CLOSESPIDER_PAGECOUNT=20 -s CLOSESPIDER_TIMEOUT=120
```

For Sport.sk:

```bash
.venv/bin/scrapy crawl sport_aktuality -a db=data/sport-aktuality-smoke.sqlite3 -s CLOSESPIDER_PAGECOUNT=20 -s CLOSESPIDER_TIMEOUT=120
```

For Koktejl.sk:

```bash
.venv/bin/scrapy crawl koktejl -a db=data/koktejl-smoke.sqlite3 -s CLOSESPIDER_PAGECOUNT=20 -s CLOSESPIDER_TIMEOUT=120
```

For Pluska.sk:

```bash
.venv/bin/scrapy crawl pluska -a db=data/pluska-smoke.sqlite3 -s CLOSESPIDER_PAGECOUNT=20 -s CLOSESPIDER_TIMEOUT=120
```

The page limit counts responses, including discovery pages, and may be exceeded slightly by in-flight requests. Full archive discovery has no page or age limit and can take a long time.

## What is collected

The Topky crawler follows the homepage, `/se/` section pagination, `/cl/` article links, robots-advertised sitemaps, and nested sitemap indexes. The Cas crawler follows its homepage, section/listing pagination, article slug paths, robots-advertised sitemaps, and nested sitemap indexes. The Pravda crawler follows its homepage, `?strana=` section pagination, numeric `/clanok/` article paths, and its multipart sitemap index. The Pravda Blog crawler follows its central sitemap and listings across author subdomains. The HN Online crawler follows its homepage and content sections plus the multipart sitemap advertised by `robots.txt`; both historical short article IDs and current numeric IDs are supported. The Sport.sk crawler follows its homepage, flat section pages, author/topic archives, and the paginated latest-news archive; articles use the numeric suffix of current `/clanok/` URLs as their IDs. The Koktejl.sk crawler follows its homepage, category and subcategory `?page=` pagination, and `/clanok/` links; articles use their case-sensitive seven-character public IDs. The Pluska crawler follows its homepage, `/r/` rubric listings, and the nested article/rubric sitemaps advertised by `robots.txt`; tracking-only `itm_*` parameters are removed and canonical article paths are used as IDs. The Živé.sk crawler follows its homepage, section listings, and any sitemaps advertised by `robots.txt`; articles use their seven-character public `/clanok/` IDs. The Diva.sk crawler follows its homepage, section pages, topic and author archives, and any sitemaps advertised by `robots.txt`; articles use their seven-character public `/clanok/` IDs. The Najmama.sk crawler follows its homepage, section pages, topic and author archives, and any sitemaps advertised by `robots.txt`; articles use their seven-character public `/clanok/` IDs. The SITA crawler follows its homepage, robots-advertised sitemaps, and all-articles RSS feed; article IDs use normalized canonical paths. The Teraz.sk crawler follows its homepage, latest-news and section listings with `?p=` pagination, robots-advertised sitemaps, and the all-news RSS feed; article IDs use the numeric value before `-clanok.html`. The Hlavné správy crawler follows the homepage, category archives and their `/page/<n>/` pagination, and robots-advertised or standard WordPress sitemaps; article IDs use the trailing numeric path segment. Every spider excludes irrelevant or offsite links according to its site-specific rules. Images are stored as URLs, not downloaded. Coverage is limited to reachable links and robots-permitted pages; this does not promise a complete historical archive.

The Cas crawler also excludes the `/horoskopy` and `/kvizy` sections, including their pagination and article URLs.

The Pravda Blog crawler follows the central multipart sitemap, blog directory pagination, author homepages, and author archive pagination across `*.blog.pravda.sk`. Dated WordPress post paths are archived as articles. WordPress administration/API paths, feeds, searches, tags, categories, comments, media assets, and non-blog Pravda subdomains are excluded. Article IDs combine the author hostname and post path so identical slugs on different blogs remain distinct. The Denník N Blog crawler starts at `/blog/` and `/zoznam-blogerov/`, follows directory-linked author profiles and their own pagination, and only queues `/blog/` articles and blog listings. Other Denník N sections and sitemaps are excluded.

Article fields include title, introduction, paragraph-preserving body text, authors, source, publication/modification timestamps, section, tags, language, image URLs, requested/final/canonical URLs, site article ID, fetch time, HTTP status, and encoding. Raw meta tags and the selected article JSON-LD object are also retained. Optional missing fields are null or empty arrays. Unparseable dates remain available in the raw metadata; timezone-less numeric dates use `Europe/Bratislava`. Topky, Pravda, and HN Online identify articles by their numeric URL IDs; Koktejl.sk uses its case-sensitive public ID; Cas and Pluska use normalized canonical article paths.

HN Online article parsing is limited to text returned in the public HTML response. The crawler does not authenticate or bypass subscription controls.

Parsing uses article JSON-LD and HTML metadata, with article-body selectors and an `<article>` fallback. Navigation, ads, related-content blocks, and scripts are removed from extracted text. A missing title or body marks the request as failed and preserves its compressed response for diagnosis.

Default requests respect robots.txt, use two concurrent downloads, a randomized two-second delay, AutoThrottle, a 30-second download timeout, a 20 MiB response limit, and three retries for transient errors. Configure Scrapy settings with `-s`, for example `-s DOWNLOAD_DELAY=5`. The user agent is `PubCrawlBot/0.2`.

## Export parsed articles

Export a schema-version-2 database as newline-delimited JSON (JSONL):

```bash
.venv/bin/python scripts/export_articles.py data/topky-v2.sqlite3 > articles.jsonl
```

The exporter streams one article at a time and writes UTF-8 JSON directly to standard output. It can also replace a named output file:

```bash
.venv/bin/python scripts/export_articles.py data/topky-v2.sqlite3 -o articles.jsonl
```

Each line contains `id` (the publisher's article ID), `url` (the final fetched URL), `text` (the parsed article body), and `meta`. The `meta` object contains the parsed title, introduction, authors, source, timestamps, section, tags, language, image URLs, and decoded raw page metadata. Crawl and internal storage fields are omitted. The input database is opened read-only and rows are exported in database article-ID order.

## Database and duplicates

| Table/view | Contents |
| --- | --- |
| `articles` | One first-saved record per publisher article ID, metadata, and content/HTML references |
| `url_aliases` | Known URL variants mapped to an article |
| `content` | Unique normalized body text and SHA-256 |
| `html_blobs` | SHA-256 and gzip-compressed response bytes |
| `crawl_queue` | Durable requests, retry counts, state, errors, and failed response references |
| `crawl_runs` | Crawl start/end, close reason, effective key settings, and Scrapy statistics |
| `crawl_attempts` | One record per dequeued request attempt, including terminal status/error |
| `duplicate_content` | Every article belonging to an exact-text duplicate group |

URL normalization removes fragments and common tracking parameters, unifies publisher host aliases to HTTPS, and sorts remaining query parameters. Pagination parameters are retained. Article IDs and validated same-article canonical links identify additional aliases. Already queued aliases are skipped once their article is saved; concurrently fetched aliases may still produce one redundant download.

Content matching includes the introduction once, normalizes Unicode to NFC, and collapses whitespace. Case, punctuation, and diacritics are significant. Different article IDs with the same normalized text remain separate records sharing a content row, so their titles, metadata, and HTML remain available. Near-duplicates are not detected. Identical HTML bytes share a blob; different HTML with identical extracted text does not.

Useful queries with the SQLite CLI:

```sql
SELECT state, count(*) FROM crawl_queue GROUP BY state;
SELECT id, title, published_at, final_url FROM articles ORDER BY id DESC LIMIT 20;
SELECT * FROM duplicate_content ORDER BY sha256, article_id;
SELECT url, retry_count, error FROM crawl_queue WHERE state IN ('failed', 'blocked');
SELECT * FROM url_aliases WHERE article_id = 1;
```

Read the exact stored HTML response bytes using Python:

```python
import gzip
import sqlite3

with sqlite3.connect("data/topky-v2.sqlite3") as db:
    row = db.execute("""
        SELECT h.data, a.encoding
        FROM articles a JOIN html_blobs h ON h.id = a.html_id
        WHERE a.id = ?
    """, (1,)).fetchone()
    if row is not None:
        html_bytes = gzip.decompress(row[0])
        html_text = html_bytes.decode(row[1] or "utf-8", errors="replace")
```

These are Scrapy's response body bytes after HTTP transfer/content decompression, before parsing or rewriting. Failed responses are accessible through `crawl_queue.html_id`.

SQLite runs with foreign keys, WAL, and `synchronous=FULL`. The scheduler persists requests before downloading them. Article writes, discovered child URLs, and parent completion share one transaction. Recovery therefore provides at-least-once downloading and idempotent article storage. Retries and redirect chains are persisted with their originating queue entry. Database errors roll back and stop the crawl. Schema version 2 is recorded in `PRAGMA user_version`; unsupported versions are rejected.

## Tests and validation limits

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Tests cover metadata extraction, missing/malformed metadata, text cleanup, Unicode, URL aliases, content duplicates, gzip round trips, locking, rollback, retries, redirects, robots exclusion, sitemap/section pagination, discovery refresh, graceful stop/resume, and forced-process termination/resume. End-to-end tests run real Scrapy subprocesses with a deterministic fixture download handler, without external or local network sockets. Fixtures are compact synthetic representations of publisher markup.

Run the bounded smoke crawl for a publisher and inspect `crawl_queue` failures before launching a full archive crawl; publisher HTML selectors, robots rules, and sitemap availability can change independently of this project.
