from app.extractor.pdf_reader import PDFReader
from app.extractor.ocr_reader import OCRReader


class TextExtractor:

    def __init__(self, pdf_path):

        self.reader = PDFReader(pdf_path)
        self.ocr = OCRReader(pdf_path)

    def extract(self):

        pages = []

        for page_number in range(self.reader.page_count()):

            has_text = self.reader.has_embedded_text(page_number)

            if has_text:

                text = self.reader.extract_text(page_number)

            else:

                # Use enhanced OCR only for Page 2
                if page_number + 1 == 2:

                    columns = self.ocr.extract_page2_columns()

                    text = f"""
LEFT COLUMN
{columns["left"]}

WEIGHT COLUMN
{columns["weight"]}

CBM COLUMN
{columns["cbm"]}
"""

                else:

                    text = self.ocr.extract_page(page_number + 1)

            pages.append(
                {
                    "page": page_number + 1,
                    "has_text": has_text,
                    "text": text,
                }
            )

        self.reader.close()

        return pages