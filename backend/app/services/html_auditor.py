import json
import logging
import os
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
PLAIN_LANGUAGE_PATH = os.path.join(DATA_DIR, "plain_language_map.json")

AXE_INJECT_SCRIPT = """
const script = document.createElement('script');
script.src = 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.0/axe.min.js';
document.head.appendChild(script);
await new Promise((resolve) => {
    script.onload = resolve;
    script.onerror = resolve;
});
"""

AXE_RUN_SCRIPT = """
const results = await axe.run(document, {
    runOnly: {
        type: 'tag',
        values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']
    }
});
return results;
"""


@dataclass
class AuditIssue:
    url: str
    severity: str
    axe_rule_id: str
    wcag_criterion: str
    plain_title: str
    plain_description: str
    fix_suggestion: str
    element_selector: str


@dataclass
class AuditResult:
    url: str
    issues: list[AuditIssue]
    error: str | None = None


class HTMLAuditor:
    def __init__(self):
        with open(PLAIN_LANGUAGE_PATH) as f:
            self.plain_map = json.load(f)

    def map_severity(self, impact: str) -> str:
        valid = {"critical", "serious", "moderate", "minor"}
        return impact if impact in valid else "moderate"

    def get_plain_language(self, rule_id: str) -> dict:
        if rule_id in self.plain_map:
            return self.plain_map[rule_id]
        title = rule_id.replace("-", " ").replace("_", " ").title()
        return {
            "title": title,
            "description": f"An accessibility issue was found ({rule_id}). This may affect users with disabilities.",
            "fix": "Ask your web administrator to review and fix this issue.",
            "wcag": "",
        }

    def _extract_wcag(self, tags: list[str]) -> str:
        for tag in tags:
            match = re.match(r"wcag(\d)(\d)(\d+)", tag)
            if match:
                return f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
        return ""

    def process_violations(self, violations: list[dict], url: str) -> list[AuditIssue]:
        issues = []
        for violation in violations:
            rule_id = violation["id"]
            severity = self.map_severity(violation.get("impact", "moderate"))
            plain = self.get_plain_language(rule_id)
            wcag = plain.get("wcag", "") or self._extract_wcag(violation.get("tags", []))

            for node in violation.get("nodes", []):
                selector = ", ".join(node.get("target", []))
                issues.append(AuditIssue(
                    url=url,
                    severity=severity,
                    axe_rule_id=rule_id,
                    wcag_criterion=wcag,
                    plain_title=plain["title"],
                    plain_description=plain["description"],
                    fix_suggestion=plain["fix"],
                    element_selector=selector,
                ))
        return issues

    async def audit_page(self, url: str) -> AuditResult:
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.evaluate(AXE_INJECT_SCRIPT)
                results = await page.evaluate(AXE_RUN_SCRIPT)
                await browser.close()

                violations = results.get("violations", [])
                issues = self.process_violations(violations, url)
                return AuditResult(url=url, issues=issues)

        except Exception as e:
            logger.warning(f"Error auditing {url}: {e}")
            return AuditResult(url=url, issues=[], error=str(e))

    async def audit_pages(self, urls: list[str], on_progress=None) -> list[AuditResult]:
        results = []
        for i, url in enumerate(urls):
            result = await self.audit_page(url)
            results.append(result)
            if on_progress:
                on_progress(i + 1, len(urls))
        return results
