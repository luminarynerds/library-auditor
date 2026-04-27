import os
import pytest
from app.services.pdf_analyzer import PDFAnalyzer, PDFAnalysisResult

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestPDFAnalyzer:
    def setup_method(self):
        self.analyzer = PDFAnalyzer()

    def test_analyze_pdf_with_text(self):
        path = os.path.join(FIXTURES, "has_text.pdf")
        result = self.analyzer.analyze_file(path)
        assert isinstance(result, PDFAnalysisResult)
        assert result.has_text is True
        assert result.page_count == 1
        assert result.file_size_bytes > 0

    def test_analyze_image_only_pdf(self):
        path = os.path.join(FIXTURES, "image_only.pdf")
        result = self.analyzer.analyze_file(path)
        assert result.has_text is False
        assert result.page_count == 1

    def test_cost_estimate_untagged(self):
        path = os.path.join(FIXTURES, "untagged.pdf")
        result = self.analyzer.analyze_file(path)
        # Untagged PDF with text: $5-15/page
        assert result.estimated_cost_low == 5.0
        assert result.estimated_cost_high == 15.0

    def test_cost_estimate_image_only_higher(self):
        path = os.path.join(FIXTURES, "image_only.pdf")
        result = self.analyzer.analyze_file(path)
        # Image-only: higher cost ($10-20/page) because OCR needed
        assert result.estimated_cost_low == 10.0
        assert result.estimated_cost_high == 20.0
