import logging
import os
import tempfile
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Issue, IssueType, IssueSeverity, PDFReport, Scan, ScanStatus
from app.services.crawler import Crawler
from app.services.html_auditor import HTMLAuditor
from app.services.pdf_analyzer import PDFAnalyzer

logger = logging.getLogger(__name__)


class ScanOrchestrator:
    def __init__(self, db: AsyncSession, scan_id):
        self.db = db
        self.scan_id = scan_id

    async def _update_status(self, status: ScanStatus, **kwargs):
        scan = await self.db.get(Scan, self.scan_id)
        scan.status = status
        for k, v in kwargs.items():
            setattr(scan, k, v)
        await self.db.commit()

    async def run(self):
        scan = await self.db.get(Scan, self.scan_id)
        if not scan:
            logger.error(f"Scan {self.scan_id} not found")
            return

        try:
            # Phase 1: Crawl
            await self._update_status(ScanStatus.crawling)
            crawler = Crawler(
                base_url=scan.base_url,
                secondary_domains=scan.secondary_urls,
            )
            crawl_result = await crawler.crawl()
            await self._update_status(
                ScanStatus.auditing,
                pages_found=len(crawl_result.html_urls),
                pdfs_found=len(crawl_result.pdf_urls),
            )

            # Phase 2: HTML audit
            auditor = HTMLAuditor()
            audit_results = await auditor.audit_pages(crawl_result.html_urls)

            # Deduplicate: track (rule, selector) pairs across pages
            # If same element appears on 2+ pages, it's a shared template issue
            seen: dict[tuple[str, str], dict] = {}  # (rule, selector) -> {issue, pages}
            for audit_result in audit_results:
                for issue in audit_result.issues:
                    key = (issue.axe_rule_id or "", issue.element_selector or "")
                    if key in seen:
                        seen[key]["pages"].add(issue.url)
                    else:
                        seen[key] = {
                            "issue": issue,
                            "pages": {issue.url},
                        }

            for key, entry in seen.items():
                issue = entry["issue"]
                pages = entry["pages"]
                if len(pages) > 1:
                    # Site-wide issue: store once with "Site-wide" prefix
                    plain_title = f"Site-wide: {issue.plain_title}"
                    url = f"{scan.base_url} (+{len(pages) - 1} more pages)"
                else:
                    plain_title = issue.plain_title
                    url = issue.url

                db_issue = Issue(
                    scan_id=self.scan_id,
                    url=url,
                    issue_type=IssueType.html,
                    severity=IssueSeverity(issue.severity),
                    axe_rule_id=issue.axe_rule_id,
                    wcag_criterion=issue.wcag_criterion,
                    plain_title=plain_title,
                    plain_description=issue.plain_description,
                    fix_suggestion=issue.fix_suggestion,
                    impact_statement=issue.impact_statement,
                    effort=issue.effort,
                    help_url=issue.help_url,
                    failure_detail=issue.failure_detail,
                    element_html=issue.element_html,
                    element_selector=issue.element_selector,
                )
                self.db.add(db_issue)
            await self.db.commit()

            # Phase 3: PDF analysis
            await self._update_status(ScanStatus.analyzing_pdfs)
            pdf_analyzer = PDFAnalyzer()
            with tempfile.TemporaryDirectory() as tmpdir:
                for pdf_url in crawl_result.pdf_urls:
                    result = await pdf_analyzer.analyze_url(pdf_url, tmpdir)
                    if result:
                        db_pdf = PDFReport(
                            scan_id=self.scan_id,
                            url=result.url,
                            filename=result.filename,
                            is_tagged=result.is_tagged,
                            has_text=result.has_text,
                            page_count=result.page_count,
                            file_size_bytes=result.file_size_bytes,
                            estimated_cost_low=result.estimated_cost_low,
                            estimated_cost_high=result.estimated_cost_high,
                        )
                        self.db.add(db_pdf)
                        if not result.is_tagged:
                            severity = IssueSeverity.critical if not result.has_text else IssueSeverity.serious
                            desc = (
                                "This PDF has no accessibility tags and contains no readable text (scanned image). "
                                "It needs OCR processing and full accessibility tagging."
                                if not result.has_text
                                else "This PDF has no accessibility tags. Screen readers cannot navigate its structure. "
                                "It needs accessibility tagging to be compliant."
                            )
                            fix = (
                                "This PDF needs to be either converted to HTML or professionally remediated. "
                                f"Estimated cost: ${result.estimated_cost_low:.0f}-${result.estimated_cost_high:.0f}."
                            )
                            pdf_issue = Issue(
                                scan_id=self.scan_id,
                                url=pdf_url,
                                issue_type=IssueType.pdf,
                                severity=severity,
                                plain_title="PDF is not accessible" if result.has_text else "PDF is a scanned image (no text)",
                                plain_description=desc,
                                fix_suggestion=fix,
                            )
                            self.db.add(pdf_issue)
            await self.db.commit()

            # Calculate compliance score
            total_pages = len(crawl_result.html_urls)
            if total_pages > 0:
                issues_result = await self.db.execute(
                    select(Issue.url).where(
                        Issue.scan_id == self.scan_id,
                        Issue.issue_type == IssueType.html,
                        Issue.severity.in_([IssueSeverity.critical, IssueSeverity.serious]),
                    ).distinct()
                )
                pages_with_critical = set(issues_result.scalars().all())
                clean_pages = total_pages - len(pages_with_critical)
                score = round((clean_pages / total_pages) * 100, 1)
            else:
                score = None

            await self._update_status(
                ScanStatus.complete,
                compliance_score=score,
                completed_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.exception(f"Scan {self.scan_id} failed: {e}")
            await self._update_status(
                ScanStatus.failed,
                error_message=str(e),
                completed_at=datetime.utcnow(),
            )
