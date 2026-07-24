import fitz
from pathlib import Path


class PDFReader:
    """
    Production PDF Reader using PyMuPDF.
    """

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)

        if not self.pdf_path.exists():
            raise FileNotFoundError(
                f"PDF not found: {self.pdf_path}"
            )

        self.document = fitz.open(self.pdf_path)

    def page_count(self):
        """Return total pages."""
        return len(self.document)

    def get_page(self, page_number: int):
        """Return a single page."""
        return self.document.load_page(page_number)

    def extract_text(self, page_number: int):
        """Extract embedded text."""
        page = self.get_page(page_number)
        return page.get_text().strip()

    def has_embedded_text(self, page_number: int):
        """Check whether page contains embedded text."""
        text = self.extract_text(page_number)
        return len(text) > 20

    def metadata(self):
        """Return PDF metadata."""
        return self.document.metadata

    def close(self):
        self.document.close()