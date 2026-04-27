import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ScanCreate(BaseModel):
    library_name: str
    base_url: str
    secondary_urls: list[str] | None = None
    access_code: str


class ScanSummary(BaseModel):
    id: uuid.UUID
    library_name: str
    base_url: str
    status: str
    error_message: str | None
    pages_found: int
    pdfs_found: int
    compliance_score: float | None
    created_at: datetime
    completed_at: datetime | None
    issue_counts: dict[str, int] | None = None

    model_config = {"from_attributes": True}


class IssueOut(BaseModel):
    id: uuid.UUID
    url: str
    issue_type: str
    severity: str
    axe_rule_id: str | None
    wcag_criterion: str | None
    plain_title: str
    plain_description: str
    fix_suggestion: str
    impact_statement: str | None
    effort: str | None
    help_url: str | None
    failure_detail: str | None
    element_html: str | None
    element_selector: str | None

    model_config = {"from_attributes": True}


class PDFReportOut(BaseModel):
    id: uuid.UUID
    url: str
    filename: str
    is_tagged: bool
    has_text: bool
    page_count: int
    file_size_bytes: int
    estimated_cost_low: Decimal
    estimated_cost_high: Decimal

    model_config = {"from_attributes": True}


class FixFirstItem(BaseModel):
    plain_title: str
    severity: str
    count: int
    fix_suggestion: str
    example_url: str
