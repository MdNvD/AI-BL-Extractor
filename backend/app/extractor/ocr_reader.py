from pdf2image import convert_from_path
import pytesseract

from app.core.config import POPPLER_PATH, TESSERACT_PATH

# Configure Tesseract
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


class OCRReader:
    """
    Extract text from scanned PDF pages using OCR.
    """

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def extract_page(self, page_number: int) -> str:
        """
        Extract text from a single page.
        """

        images = convert_from_path(
            self.pdf_path,
            first_page=page_number,
            last_page=page_number,
            dpi=300,
            poppler_path=POPPLER_PATH
        )

        image = images[0]

        text = pytesseract.image_to_string(
            image,
            lang="eng"
        )

        return text.strip()

    def extract_page2_columns(self):
        """
        Extract Page 2 by splitting it into
        Left | Weight | CBM columns.
        """

        images = convert_from_path(
            self.pdf_path,
            first_page=2,
            last_page=2,
            dpi=400,
            poppler_path=POPPLER_PATH
        )

        image = images[0]

        width, height = image.size

        left = image.crop((0, 0, int(width * 0.68), height))
        weight = image.crop((int(width * 0.68), 0, int(width * 0.86), height))
        cbm = image.crop((int(width * 0.84), 0, width, height))

        left = left.resize((left.width * 2, left.height * 2))
        weight = weight.resize((weight.width * 2, weight.height * 2))
        cbm = cbm.resize((cbm.width * 2, cbm.height * 2))

        config = "--oem 3 --psm 6"

        left_text = pytesseract.image_to_string(
            left,
            lang="eng",
            config=config
        )

        weight_text = pytesseract.image_to_string(
            weight,
            lang="eng",
            config=config
        )

        cbm_text = pytesseract.image_to_string(
            cbm,
            lang="eng",
            config=config
        )

        return {
            "left": left_text,
            "weight": weight_text,
            "cbm": cbm_text
        }