import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.crawler import Crawler, DiscoveredURL


@pytest.fixture
def crawler():
    return Crawler(base_url="https://example-library.org", rate_limit=100.0, max_pages=10, max_depth=3)


class TestURLClassification:
    def test_html_page_detected(self, crawler):
        result = crawler.classify_url("https://example-library.org/about")
        assert result == "html"

    def test_pdf_by_extension(self, crawler):
        result = crawler.classify_url("https://example-library.org/docs/report.pdf")
        assert result == "pdf"

    def test_pdf_case_insensitive(self, crawler):
        result = crawler.classify_url("https://example-library.org/docs/REPORT.PDF")
        assert result == "pdf"


class TestDomainFiltering:
    def test_same_domain_allowed(self, crawler):
        assert crawler.is_allowed_domain("https://example-library.org/page") is True

    def test_external_domain_blocked(self, crawler):
        assert crawler.is_allowed_domain("https://nytimes.com/article") is False

    def test_secondary_domain_allowed(self):
        c = Crawler(
            base_url="https://example-library.org",
            secondary_domains=["example-library.libguides.com"],
            rate_limit=100.0,
            max_pages=10,
            max_depth=3,
        )
        assert c.is_allowed_domain("https://example-library.libguides.com/guide1") is True


class TestLinkExtraction:
    def test_extracts_links_from_html(self, crawler):
        html = """
        <html><body>
            <a href="/about">About</a>
            <a href="https://example-library.org/events">Events</a>
            <a href="https://external.com">External</a>
            <a href="/files/report.pdf">Report</a>
        </body></html>
        """
        links = crawler.extract_links(html, "https://example-library.org/")
        urls = [link.url for link in links]
        assert "https://example-library.org/about" in urls
        assert "https://example-library.org/events" in urls
        assert "https://example-library.org/files/report.pdf" in urls
        assert "https://external.com" not in urls
