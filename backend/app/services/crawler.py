import asyncio
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from robotexclusionrulesparser import RobotExclusionRulesParser

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredURL:
    url: str
    url_type: str  # "html" or "pdf"
    depth: int


@dataclass
class CrawlResult:
    html_urls: list[str] = field(default_factory=list)
    pdf_urls: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class Crawler:
    def __init__(
        self,
        base_url: str,
        secondary_domains: list[str] | None = None,
        rate_limit: float = 2.0,
        max_pages: int = 500,
        max_depth: int = 5,
    ):
        self.base_url = base_url.rstrip("/")
        parsed = urlparse(self.base_url)
        self.allowed_domains = {parsed.hostname}
        if secondary_domains:
            for d in secondary_domains:
                self.allowed_domains.add(d.lower())
        self.rate_limit = rate_limit
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.visited: set[str] = set()
        self.robots_cache: dict[str, RobotExclusionRulesParser] = {}

    def classify_url(self, url: str) -> str:
        path = urlparse(url).path.lower()
        if path.endswith(".pdf"):
            return "pdf"
        return "html"

    def is_allowed_domain(self, url: str) -> bool:
        hostname = urlparse(url).hostname
        if hostname is None:
            return False
        return hostname.lower() in self.allowed_domains

    def normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        normalized = parsed._replace(fragment="").geturl().rstrip("/")
        return normalized

    def extract_links(self, html: str, page_url: str) -> list[DiscoveredURL]:
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            absolute = urljoin(page_url, href)
            absolute = self.normalize_url(absolute)
            if self.is_allowed_domain(absolute):
                links.append(DiscoveredURL(
                    url=absolute,
                    url_type=self.classify_url(absolute),
                    depth=0,
                ))
        return links

    async def _check_robots(self, client: httpx.AsyncClient, url: str) -> bool:
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.hostname}"
        if domain not in self.robots_cache:
            parser = RobotExclusionRulesParser()
            try:
                resp = await client.get(f"{domain}/robots.txt", timeout=10)
                if resp.status_code == 200:
                    parser.parse(resp.text)
                else:
                    parser.parse("")
            except Exception:
                parser.parse("")
            self.robots_cache[domain] = parser
        return self.robots_cache[domain].is_allowed("*", url)

    async def _fetch_sitemap_urls(self, client: httpx.AsyncClient) -> list[str]:
        """Try to find and parse sitemap.xml for the site."""
        urls = []
        sitemap_locations = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/sitemap_index.xml",
        ]

        # Also check robots.txt for Sitemap directives
        try:
            resp = await client.get(f"{self.base_url}/robots.txt", timeout=10)
            if resp.status_code == 200:
                for line in resp.text.splitlines():
                    line = line.strip()
                    if line.lower().startswith("sitemap:"):
                        sitemap_url = line.split(":", 1)[1].strip()
                        if sitemap_url not in sitemap_locations:
                            sitemap_locations.insert(0, sitemap_url)
        except Exception:
            pass

        for sitemap_url in sitemap_locations:
            try:
                resp = await client.get(sitemap_url, timeout=15)
                if resp.status_code != 200:
                    continue
                found = self._parse_sitemap(resp.text, client)
                if asyncio.iscoroutine(found):
                    found = await found
                urls.extend(found)
                if urls:
                    logger.info(f"Found {len(urls)} URLs from sitemap: {sitemap_url}")
                    break
            except Exception as e:
                logger.debug(f"Sitemap fetch failed for {sitemap_url}: {e}")

        return urls

    async def _parse_sitemap(self, xml_text: str, client: httpx.AsyncClient) -> list[str]:
        """Parse sitemap XML, handling both sitemap indexes and url sets."""
        urls = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return urls

        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        # Check if this is a sitemap index (contains other sitemaps)
        sub_sitemaps = root.findall(".//sm:sitemap/sm:loc", ns)
        if sub_sitemaps:
            for loc in sub_sitemaps[:5]:  # limit to 5 sub-sitemaps
                try:
                    resp = await client.get(loc.text.strip(), timeout=15)
                    if resp.status_code == 200:
                        sub_urls = await self._parse_sitemap(resp.text, client)
                        urls.extend(sub_urls)
                except Exception:
                    continue
            return urls

        # Regular sitemap with <url><loc> entries
        for loc in root.findall(".//sm:url/sm:loc", ns):
            url = loc.text.strip() if loc.text else ""
            if url and self.is_allowed_domain(url):
                urls.append(self.normalize_url(url))

        # Try without namespace (some sitemaps don't use it)
        if not urls:
            for loc in root.findall(".//url/loc"):
                url = loc.text.strip() if loc.text else ""
                if url and self.is_allowed_domain(url):
                    urls.append(self.normalize_url(url))

        return urls

    async def _playwright_extract_links(self, url: str) -> list[str]:
        """Use Playwright to render a page and extract links from JS-rendered content."""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)
                links = await page.evaluate("""
                    () => Array.from(document.querySelectorAll('a[href]'))
                        .map(a => a.href)
                        .filter(href => href.startsWith('http'))
                """)
                await browser.close()
                return links
        except Exception as e:
            logger.warning(f"Playwright link extraction failed for {url}: {e}")
            return []

    async def crawl(self, on_progress=None) -> CrawlResult:
        result = CrawlResult()
        delay = 1.0 / self.rate_limit

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            headers={"User-Agent": "LibraryAuditor/1.0 (+https://github.com/library-auditor)"},
        ) as client:
            # Phase 1: Try sitemap first
            sitemap_urls = await self._fetch_sitemap_urls(client)
            if sitemap_urls:
                logger.info(f"Sitemap discovery: {len(sitemap_urls)} URLs found")
                for url in sitemap_urls[:self.max_pages]:
                    normalized = self.normalize_url(url)
                    if normalized in self.visited:
                        continue
                    self.visited.add(normalized)
                    url_type = self.classify_url(normalized)
                    if url_type == "pdf":
                        result.pdf_urls.append(normalized)
                    else:
                        result.html_urls.append(normalized)
                    if on_progress:
                        on_progress(len(result.html_urls), len(result.pdf_urls))
            else:
                logger.info("No sitemap found, falling back to crawl")

            # Phase 2: Crawl starting from base URL (and any sitemap pages)
            # Use Playwright on the home page to find JS-rendered links
            if not sitemap_urls:
                pw_links = await self._playwright_extract_links(self.base_url)
                queue: list[tuple[str, int]] = [(self.base_url, 0)]
                for link in pw_links:
                    normalized = self.normalize_url(link)
                    if self.is_allowed_domain(normalized) and normalized not in self.visited:
                        queue.append((normalized, 1))
            else:
                # Even with sitemap, crawl the base URL for any links not in sitemap
                queue = [(self.base_url, 0)]

            while queue and len(self.visited) < self.max_pages:
                url, depth = queue.pop(0)
                normalized = self.normalize_url(url)

                if normalized in self.visited:
                    continue
                if depth > self.max_depth:
                    continue

                self.visited.add(normalized)

                if not await self._check_robots(client, normalized):
                    logger.debug(f"Blocked by robots.txt: {normalized}")
                    continue

                url_type = self.classify_url(normalized)
                if url_type == "pdf":
                    result.pdf_urls.append(normalized)
                    if on_progress:
                        on_progress(len(result.html_urls), len(result.pdf_urls))
                    continue

                try:
                    await asyncio.sleep(delay)
                    resp = await client.get(normalized, timeout=30)
                    content_type = resp.headers.get("content-type", "")

                    if "application/pdf" in content_type:
                        result.pdf_urls.append(normalized)
                        if on_progress:
                            on_progress(len(result.html_urls), len(result.pdf_urls))
                        continue

                    if "text/html" not in content_type:
                        continue

                    result.html_urls.append(normalized)
                    if on_progress:
                        on_progress(len(result.html_urls), len(result.pdf_urls))

                    # Extract links from HTML
                    links = self.extract_links(resp.text, normalized)
                    for link in links:
                        link_normalized = self.normalize_url(link.url)
                        if link_normalized not in self.visited:
                            queue.append((link_normalized, depth + 1))

                except Exception as e:
                    error_msg = f"Error crawling {normalized}: {str(e)}"
                    logger.warning(error_msg)
                    result.errors.append(error_msg)

        return result
