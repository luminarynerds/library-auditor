import asyncio
import logging
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

    async def crawl(self, on_progress=None) -> CrawlResult:
        result = CrawlResult()
        queue: list[tuple[str, int]] = [(self.base_url, 0)]
        delay = 1.0 / self.rate_limit

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            headers={"User-Agent": "LibraryAuditor/1.0 (+https://github.com/library-auditor)"},
        ) as client:
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
