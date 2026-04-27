import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ScanStatus(str, enum.Enum):
    queued = "queued"
    crawling = "crawling"
    auditing = "auditing"
    analyzing_pdfs = "analyzing_pdfs"
    complete = "complete"
    failed = "failed"


class IssueSeverity(str, enum.Enum):
    critical = "critical"
    serious = "serious"
    moderate = "moderate"
    minor = "minor"


class IssueType(str, enum.Enum):
    html = "html"
    pdf = "pdf"


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    library_name: Mapped[str] = mapped_column(String(255))
    base_url: Mapped[str] = mapped_column(String(2048))
    secondary_urls: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    status: Mapped[ScanStatus] = mapped_column(Enum(ScanStatus), default=ScanStatus.queued)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    pages_found: Mapped[int] = mapped_column(Integer, default=0)
    pdfs_found: Mapped[int] = mapped_column(Integer, default=0)
    compliance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    issues: Mapped[list["Issue"]] = relationship(back_populates="scan", cascade="all, delete-orphan")
    pdf_reports: Mapped[list["PDFReport"]] = relationship(back_populates="scan", cascade="all, delete-orphan")


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(String(2048))
    issue_type: Mapped[IssueType] = mapped_column(Enum(IssueType))
    severity: Mapped[IssueSeverity] = mapped_column(Enum(IssueSeverity))
    axe_rule_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    wcag_criterion: Mapped[str | None] = mapped_column(String(20), nullable=True)
    plain_title: Mapped[str] = mapped_column(String(255))
    plain_description: Mapped[str] = mapped_column(Text)
    fix_suggestion: Mapped[str] = mapped_column(Text)
    impact_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    effort: Mapped[str | None] = mapped_column(String(20), nullable=True)
    help_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    failure_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    element_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    element_selector: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    scan: Mapped["Scan"] = relationship(back_populates="issues")


class PDFReport(Base):
    __tablename__ = "pdf_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(String(2048))
    filename: Mapped[str] = mapped_column(String(512))
    is_tagged: Mapped[bool] = mapped_column(Boolean)
    has_text: Mapped[bool] = mapped_column(Boolean)
    page_count: Mapped[int] = mapped_column(Integer)
    file_size_bytes: Mapped[int] = mapped_column(Integer)
    estimated_cost_low: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    estimated_cost_high: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    scan: Mapped["Scan"] = relationship(back_populates="pdf_reports")
