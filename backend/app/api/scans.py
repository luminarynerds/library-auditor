import time
import uuid
from collections import defaultdict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Issue, IssueSeverity, IssueType, PDFReport, Scan, ScanStatus
from app.schemas import FixFirstItem, IssueOut, PDFReportOut, ScanCreate, ScanSummary
from app.services.scan_orchestrator import ScanOrchestrator

router = APIRouter(prefix="/scans", tags=["scans"])

# Simple in-memory rate limiting
_rate_limit: dict[str, float] = {}
RATE_LIMIT_SECONDS = 3600


def _check_rate_limit(client_ip: str):
    now = time.time()
    last = _rate_limit.get(client_ip, 0)
    if now - last < RATE_LIMIT_SECONDS:
        remaining = int(RATE_LIMIT_SECONDS - (now - last))
        raise HTTPException(
            status_code=429,
            detail=f"Rate limited. Try again in {remaining} seconds.",
        )
    _rate_limit[client_ip] = now


async def _run_scan(scan_id: uuid.UUID):
    from app.database import async_session

    async with async_session() as db:
        orchestrator = ScanOrchestrator(db, scan_id)
        await orchestrator.run()


@router.post("", response_model=ScanSummary, status_code=201)
async def create_scan(
    body: ScanCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    if body.access_code != settings.access_code:
        raise HTTPException(status_code=403, detail="Invalid access code.")

    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    scan = Scan(
        library_name=body.library_name,
        base_url=body.base_url.rstrip("/"),
        secondary_urls=body.secondary_urls,
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    background_tasks.add_task(_run_scan, scan.id)

    return ScanSummary.model_validate(scan)


@router.get("/{scan_id}", response_model=ScanSummary)
async def get_scan(scan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    scan = await db.get(Scan, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")

    counts_result = await db.execute(
        select(Issue.severity, func.count(Issue.id))
        .where(Issue.scan_id == scan_id)
        .group_by(Issue.severity)
    )
    issue_counts = {row[0].value: row[1] for row in counts_result.all()}

    summary = ScanSummary.model_validate(scan)
    summary.issue_counts = issue_counts
    return summary


@router.get("/{scan_id}/issues", response_model=list[IssueOut])
async def get_issues(
    scan_id: uuid.UUID,
    severity: str | None = None,
    issue_type: str | None = None,
    page: int = 1,
    per_page: int = 50,
    db: AsyncSession = Depends(get_db),
):
    scan = await db.get(Scan, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")

    query = select(Issue).where(Issue.scan_id == scan_id)
    if severity:
        query = query.where(Issue.severity == IssueSeverity(severity))
    if issue_type:
        query = query.where(Issue.issue_type == IssueType(issue_type))
    query = query.order_by(
        Issue.severity,
        Issue.url,
    ).offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    return [IssueOut.model_validate(i) for i in result.scalars().all()]


@router.get("/{scan_id}/pdfs", response_model=list[PDFReportOut])
async def get_pdfs(
    scan_id: uuid.UUID,
    page: int = 1,
    per_page: int = 50,
    db: AsyncSession = Depends(get_db),
):
    scan = await db.get(Scan, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")

    query = (
        select(PDFReport)
        .where(PDFReport.scan_id == scan_id)
        .order_by(PDFReport.is_tagged, desc(PDFReport.page_count))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    return [PDFReportOut.model_validate(p) for p in result.scalars().all()]


@router.get("/{scan_id}/fix-first", response_model=list[FixFirstItem])
async def get_fix_first(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    scan = await db.get(Scan, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")

    result = await db.execute(
        select(
            Issue.plain_title,
            Issue.severity,
            Issue.fix_suggestion,
            Issue.url,
            func.count(Issue.id).label("count"),
        )
        .where(Issue.scan_id == scan_id)
        .group_by(Issue.plain_title, Issue.severity, Issue.fix_suggestion, Issue.url)
        .order_by(Issue.severity, desc("count"))
        .limit(10)
    )

    items = []
    seen_titles = set()
    for row in result.all():
        if row.plain_title in seen_titles:
            continue
        seen_titles.add(row.plain_title)
        items.append(FixFirstItem(
            plain_title=row.plain_title,
            severity=row.severity.value,
            count=row.count,
            fix_suggestion=row.fix_suggestion,
            example_url=row.url,
        ))

    return items[:10]
