import logging
import os
from dataclasses import dataclass
from decimal import Decimal

import fitz  # PyMuPDF
import httpx

logger = logging.getLogger(__name__)


@dataclass
class PDFAnalysisResult:
    url: str
    filename: str
    is_tagged: bool
    has_text: bool
    page_count: int
    file_size_bytes: int
    estimated_cost_low: float
    estimated_cost_high: float


class PDFAnalyzer:
    def __init__(self, max_size_mb: int = 50):
        self.max_size_bytes = max_size_mb * 1024 * 1024

    def analyze_file(self, path: str, url: str = "") -> PDFAnalysisResult:
        file_size = os.path.getsize(path)
        doc = fitz.open(path)
        try:
            page_count = len(doc)
            is_tagged = self._check_tagged(doc)
            has_text = self._check_has_text(doc)
            cost_low, cost_high = self._estimate_cost(page_count, is_tagged, has_text)
            filename = os.path.basename(url) if url else os.path.basename(path)

            return PDFAnalysisResult(
                url=url,
                filename=filename,
                is_tagged=is_tagged,
                has_text=has_text,
                page_count=page_count,
                file_size_bytes=file_size,
                estimated_cost_low=cost_low,
                estimated_cost_high=cost_high,
            )
        finally:
            doc.close()

    def _check_tagged(self, doc: fitz.Document) -> bool:
        try:
            catalog = doc.pdf_catalog()
            if catalog == 0:
                return False
            for key in ["StructTreeRoot", "MarkInfo"]:
                val = doc.xref_get_key(catalog, key)
                if val[0] != "null":
                    return True
            return False
        except Exception:
            return False

    def _check_has_text(self, doc: fitz.Document) -> bool:
        pages_to_check = min(len(doc), 5)
        for i in range(pages_to_check):
            text = doc[i].get_text().strip()
            if len(text) > 10:
                return True
        return False

    def _estimate_cost(self, page_count: int, is_tagged: bool, has_text: bool) -> tuple[float, float]:
        if is_tagged:
            return (0.0, 0.0)
        if not has_text:
            return (page_count * 10.0, page_count * 20.0)
        return (page_count * 5.0, page_count * 15.0)

    async def analyze_url(self, url: str, download_dir: str) -> PDFAnalysisResult | None:
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"Failed to download PDF {url}: {resp.status_code}")
                    return None
                if len(resp.content) > self.max_size_bytes:
                    logger.warning(f"PDF too large ({len(resp.content)} bytes): {url}")
                    return None

                filename = os.path.basename(url.split("?")[0]) or "unknown.pdf"
                path = os.path.join(download_dir, filename)
                with open(path, "wb") as f:
                    f.write(resp.content)

                result = self.analyze_file(path, url=url)
                os.remove(path)
                return result
        except Exception as e:
            logger.warning(f"Error analyzing PDF {url}: {e}")
            return None
