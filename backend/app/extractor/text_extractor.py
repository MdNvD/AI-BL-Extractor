from app.extractor.pdf_reader import PDFReader
from app.extractor.ocr_reader import OCRReader


class TextExtractor:
    """
    Extract text from every page of a Bill of Lading.

    Digital PDF:
        PyMuPDF -> PDFReader

    Scanned/image content:
        Poppler -> Tesseract -> OCRReader

    For clearly digital pages, OCR is skipped to avoid
    unnecessary processing and OCR noise.

    For scanned pages with little or no embedded text,
    Tesseract OCR is used.

    Both embedded PDF text and OCR text are retained
    in the final page structure.
    """

    def __init__(self, pdf_path):
        self.reader = PDFReader(pdf_path)
        self.ocr = OCRReader(pdf_path)

    def extract(self):
        pages = []

        total_pages = self.reader.page_count()

        print(f"PDF pages detected: {total_pages}")

        for page_number in range(total_pages):

            page_index = page_number + 1

            print(f"\nProcessing page {page_index}/{total_pages}")

            # ----------------------------------------------
            # Step 1: Extract embedded PDF text
            # ----------------------------------------------

            try:
                embedded_text = (
                    self.reader.extract_text(page_number) or ""
                )
            except Exception as e:
                print(
                    f"PyMuPDF extraction failed on page "
                    f"{page_index}: {e}"
                )
                embedded_text = ""

            embedded_text = embedded_text.strip()

            # ----------------------------------------------
            # Step 2: Decide whether OCR is required
            # ----------------------------------------------

            has_embedded_text = len(embedded_text) > 20

            if has_embedded_text:

                print(
                    f"Embedded text detected on page "
                    f"{page_index}. Skipping OCR."
                )

                ocr_text = ""

            else:

                print(
                    f"Little or no embedded text on page "
                    f"{page_index}. Running OCR..."
                )

                # ------------------------------------------
                # Step 3: OCR scanned/image page
                # ------------------------------------------

                try:
                    ocr_text = (
                        self.ocr.extract_page(page_index) or ""
                    )
                except Exception as e:
                    print(
                        f"OCR failed on page "
                        f"{page_index}: {e}"
                    )
                    ocr_text = ""

                ocr_text = ocr_text.strip()

            # ----------------------------------------------
            # Step 4: Build complete page text
            # ----------------------------------------------

            combined_text = (
                f"--- PAGE {page_index} ---\n\n"
                f"--- EMBEDDED PDF TEXT ---\n"
                f"{embedded_text}\n\n"
                f"--- OCR TEXT ---\n"
                f"{ocr_text}"
            )

            # ----------------------------------------------
            # Step 5: Store page information
            # ----------------------------------------------

            pages.append(
                {
                    "page": page_index,
                    "has_text": bool(embedded_text),
                    "embedded_text": embedded_text,
                    "ocr_text": ocr_text,
                    "text": combined_text,
                }
            )

            # ----------------------------------------------
            # Logging
            # ----------------------------------------------

            print(
                f"Embedded text characters: "
                f"{len(embedded_text)}"
            )

            print(
                f"OCR text characters: "
                f"{len(ocr_text)}"
            )

            print(
                f"Combined text characters: "
                f"{len(combined_text)}"
            )

        # ----------------------------------------------
        # Close PDF
        # ----------------------------------------------

        self.reader.close()

        return pages