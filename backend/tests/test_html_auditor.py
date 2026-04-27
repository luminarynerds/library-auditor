import json
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.html_auditor import HTMLAuditor, AuditResult

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "data", "plain_language_map.json")


class TestHTMLAuditor:
    def setup_method(self):
        self.auditor = HTMLAuditor()

    def test_map_severity(self):
        assert self.auditor.map_severity("critical") == "critical"
        assert self.auditor.map_severity("serious") == "serious"
        assert self.auditor.map_severity("moderate") == "moderate"
        assert self.auditor.map_severity("minor") == "minor"

    def test_get_plain_language_known_rule(self):
        result = self.auditor.get_plain_language("image-alt")
        assert result["title"] == "Image missing description"
        assert "fix" in result
        assert "description" in result

    def test_get_plain_language_unknown_rule(self):
        result = self.auditor.get_plain_language("some-unknown-rule-xyz")
        assert "title" in result
        assert result["title"] != ""

    def test_get_plain_language_has_new_fields(self):
        result = self.auditor.get_plain_language("image-alt")
        assert "impact" in result
        assert "effort" in result
        assert "help_url" in result
        assert result["effort"] in ("quick", "developer", "redesign")

    def test_process_axe_results(self):
        fake_violations = [
            {
                "id": "image-alt",
                "impact": "critical",
                "tags": ["wcag2a", "wcag111"],
                "nodes": [
                    {
                        "target": ["img.logo"],
                        "html": "<img src='logo.png'>",
                        "failureSummary": "Fix any of the following: Element does not have an alt attribute",
                    }
                ],
            }
        ]
        issues = self.auditor.process_violations(fake_violations, "https://example.org/")
        assert len(issues) == 1
        assert issues[0].severity == "critical"
        assert issues[0].plain_title == "Image missing description"
        assert issues[0].url == "https://example.org/"
        assert issues[0].impact_statement != ""
        assert issues[0].effort == "quick"
        assert "dequeuniversity" in issues[0].help_url
        assert issues[0].failure_detail == "Fix any of the following: Element does not have an alt attribute"
        assert issues[0].element_html == "<img src='logo.png'>"
