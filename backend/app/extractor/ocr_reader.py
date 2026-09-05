from pdf2image import convert_from_path
import pytesseract

from PIL import ImageOps, ImageEnhance

from app.core.config import POPPLER_PATH, TESSERACT_PATH


# Configure Tesseract only when a custom path is provided.
# On Linux/Docker, Tesseract is installed system-wide and
# pytesseract can use the default executable.
if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


class OCRReader:
    """
    OCR reader for scanned Bill of Lading pages.

    The complete page is processed as one image.
    We do not crop the page into separate columns,
    because doing so can destroy the relationship
    between container, seal, cartons, weight and CBM.

    Primary OCR uses Tesseract PSM 6.

    A PSM 3 fallback is used only when the primary
    OCR result appears clearly incomplete.

    Before OCR, the scanned page is lightly preprocessed
    to improve recognition of small or faint text.
    """

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def _preprocess_image(self, image):
        """
        Preprocess scanned BL page before OCR.

        Processing:
        1. Convert to grayscale
        2. Improve overall contrast
        3. Slightly enhance contrast
        4. Upscale the image

        The complete page is preserved.
        No cropping is performed because container,
        seal, cartons, weight and CBM relationships
        must remain intact.
        """

        # ----------------------------------------------
        # Step 1: Convert to grayscale
        # ----------------------------------------------

        image = ImageOps.grayscale(image)

        # ----------------------------------------------
        # Step 2: Improve overall contrast
        # ----------------------------------------------

        image = ImageOps.autocontrast(image)

        # ----------------------------------------------
        # Step 3: Slightly enhance contrast
        # ----------------------------------------------

        image = ImageEnhance.Contrast(image).enhance(1.2)

        # ----------------------------------------------
        # Step 4: Upscale image
        # ----------------------------------------------

        width, height = image.size

        image = image.resize(
            (width * 2, height * 2)
        )

        return image

    def _run_ocr(self, image, psm: int) -> str:
        """
        Run Tesseract OCR using the requested page
        segmentation mode.
        """

        config = f"--oem 3 --psm {psm}"

        text = pytesseract.image_to_string(
            image,
            lang="eng",
            config=config
        )

        return text.strip()

    def _needs_fallback(self, text: str) -> bool:
        """
        Decide whether the primary OCR result looks
        clearly incomplete.

        This is intentionally conservative so that
        good PSM 6 results are not unnecessarily
        processed again.
        """

        if not text:
            return True

        # Very small OCR output usually means that
        # Tesseract failed to recognize the page.
        if len(text) < 300:
            return True

        upper_text = text.upper()

        # Common BL-related indicators.
        indicators = [
            "CONTAINER",
            "CONTAINER NOS",
            "CONT/SEALS",
            "B/L",
            "BILL OF LADING",
            "SHIPPER",
            "CONSIGNEE",
            "VESSEL",
            "VOYAGE",
            "CARTONS",
            "KGM",
            "CBM",
            "SEAL",
        ]

        indicator_count = sum(
            1
            for indicator in indicators
            if indicator in upper_text
        )

        # If the page contains enough text but none
        # of the expected BL indicators, try fallback.
        if len(text) < 800 and indicator_count == 0:
            return True

        return False

    def _select_better_result(
        self,
        primary_text: str,
        fallback_text: str
    ) -> str:
        """
        Select the better OCR result.

        Prefer the fallback only when it produces
        substantially more usable text.
        """

        if not primary_text:
            return fallback_text

        if not fallback_text:
            return primary_text

        primary_score = len(primary_text)
        fallback_score = len(fallback_text)

        # Prefer fallback when it provides at least
        # 20% more OCR text.
        if fallback_score >= primary_score * 1.20:
            return fallback_text

        return primary_text

    def extract_page(self, page_number: int) -> str:
        """
        Extract text from one complete PDF page.

        The entire page is passed to Tesseract so that
        table information remains together.
        """

        # ----------------------------------------------
        # Step 1: Convert PDF page to image
        # ----------------------------------------------

        conversion_options = {
            "first_page": page_number,
            "last_page": page_number,
            "dpi": 400,
        }

        # Use custom Poppler path only when configured.
        # On Linux/Docker, pdf2image will use the system
        # Poppler installation.
        if POPPLER_PATH:
            conversion_options["poppler_path"] = POPPLER_PATH

        images = convert_from_path(
            self.pdf_path,
            **conversion_options
        )

        if not images:
            return ""

        image = images[0]

        # ----------------------------------------------
        # Step 2: Preprocess image
        # ----------------------------------------------

        processed_image = self._preprocess_image(image)

        # ----------------------------------------------
        # Step 3: Primary OCR using PSM 6
        # ----------------------------------------------

        primary_text = self._run_ocr(
            processed_image,
            psm=6
        )

        print(
            f"OCR PSM 6 characters on page "
            f"{page_number}: {len(primary_text)}"
        )

        # ----------------------------------------------
        # Step 4: Check whether fallback is needed
        # ----------------------------------------------

        if not self._needs_fallback(primary_text):

            print(
                f"OCR PSM 6 accepted on page "
                f"{page_number}."
            )

            return primary_text

        # ----------------------------------------------
        # Step 5: Fallback OCR using PSM 3
        # ----------------------------------------------

        print(
            f"OCR PSM 6 appears incomplete on page "
            f"{page_number}. Running PSM 3 fallback..."
        )

        fallback_text = self._run_ocr(
            processed_image,
            psm=3
        )

        print(
            f"OCR PSM 3 characters on page "
            f"{page_number}: {len(fallback_text)}"
        )

        # ----------------------------------------------
        # Step 6: Select better OCR result
        # ----------------------------------------------

        selected_text = self._select_better_result(
            primary_text,
            fallback_text
        )

        if selected_text == fallback_text:
            print(
                f"OCR PSM 3 selected for page "
                f"{page_number}."
            )
        else:
            print(
                f"OCR PSM 6 retained for page "
                f"{page_number}."
            )

        return selected_text