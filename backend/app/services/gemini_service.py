import re
import time
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from app.core.config import GEMINI_API_KEY
from app.utils.prompt_manager import load_prompt
from app.utils.json_parser import parse_json


class GeminiService:
    """
    Bill of Lading extraction and validation service.

    Responsibilities:
        1. Header / shipment information extraction using Gemini
        2. Container extraction using Gemini
        3. Explicit document-total extraction using Python
        4. Container validation using Python
        5. Safe normalization of Gemini/OCR output

    IMPORTANT:
        - Gemini extracts document information.
        - Python performs calculations.
        - Python does NOT invent missing values.
        - Calculated totals are used only for validation.
        - Document totals are taken only from explicitly printed
          shipment-level totals in the Bill of Lading.
    """

    HEADER_FIELDS = [
        "carrier",
        "shipper",
        "consignee",
        "notify_party",
        "also_notify",
        "forwarding_agent",
        "consignee_reference",
        "carrier_reference",
        "bill_of_lading_number",
        "booking_number",
        "bl_type",
        "issue_date",
        "issue_place",
        "original_bl_count",
        "vessel",
        "voyage",
        "port_of_loading",
        "port_of_discharge",
        "place_of_receipt",
        "place_of_delivery",
        "freight",
        "cargo_description",
        "marks_and_numbers",
        "temperature",
        "net_weight_kg",
        "gross_weight_kg",
        "form_m_number",
        "special_instructions",
        "free_time",
    ]

    CONTAINER_FIELDS = [
        "container_number",
        "seal_number",
        "size",
        "cartons",
        "weight_kg",
        "cbm",
    ]

    SUMMARY_FIELDS = [
        "total_containers",
        "total_cartons",
        "total_weight",
        "total_cbm",
    ]

    MISSING_VALUES = {
        "",
        "-",
        "--",
        "N/A",
        "NA",
        "NULL",
        "NONE",
        "NOT PROVIDED",
        "NOT AVAILABLE",
        "NOT APPLICABLE",
        "UNKNOWN",
    }

    def __init__(self):

        if not GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        self.models = [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
        ]

    # ==========================================================
    # GEMINI GENERATION
    # ==========================================================

    def _generate(
        self,
        prompt: str,
        text: str,
    ) -> Dict[str, Any]:
        """
        Send the complete Bill of Lading text to Gemini.

        Gemini is instructed to return JSON only.

        Retry strategy:
            - temporary errors -> retry
            - 429 / quota -> switch model
            - 503 -> retry and then switch model
        """

        if not text or not text.strip():
            raise ValueError(
                "Cannot perform Gemini extraction because "
                "document text is empty."
            )

        last_error = None

        request = f"""
{prompt}

==================================================
CRITICAL SYSTEM RULES
==================================================

1. Examine the COMPLETE document below.
2. Use ONLY information explicitly supported by the document.
3. Do NOT calculate missing values.
4. Do NOT infer missing values.
5. Do NOT copy one field into another.
6. Do NOT replace document values with common values.
7. Preserve actual document wording where the prompt requires it.
8. Return ONLY valid JSON.
9. Do not return Markdown.
10. Do not return code fences.
11. Do not return explanations.

==================================================
COMPLETE BILL OF LADING DOCUMENT
==================================================

{text}

==================================================
END COMPLETE BILL OF LADING DOCUMENT
==================================================
"""

        for model in self.models:

            for attempt in range(3):

                try:

                    print(
                        f"\nUsing {model} "
                        f"(Attempt {attempt + 1}/3)"
                    )

                    response = self.client.models.generate_content(
                        model=model,
                        contents=request,
                        config=types.GenerateContentConfig(
                            temperature=0,
                            response_mime_type="application/json",
                        ),
                    )

                    if not response:
                        raise RuntimeError(
                            "Gemini returned no response."
                        )

                    response_text = getattr(
                        response,
                        "text",
                        None,
                    )

                    if not response_text:
                        raise RuntimeError(
                            "Gemini returned an empty response."
                        )

                    result = parse_json(
                        response_text
                    )

                    if not isinstance(result, dict):
                        raise RuntimeError(
                            "Gemini returned JSON, but the "
                            "top-level result is not an object."
                        )

                    return result

                except Exception as exc:

                    last_error = exc

                    error_text = str(
                        exc
                    ).upper()

                    print(
                        f"{model} failed: {exc}"
                    )

                    # ------------------------------------------
                    # Quota / rate limit
                    # ------------------------------------------

                    if (
                        "429" in error_text
                        or
                        "RESOURCE_EXHAUSTED" in error_text
                        or
                        "QUOTA" in error_text
                    ):

                        print(
                            f"{model} quota/rate limit encountered."
                        )

                        break

                    # ------------------------------------------
                    # Temporary server errors
                    # ------------------------------------------

                    temporary_error = any(
                        code in error_text
                        for code in [
                            "503",
                            "UNAVAILABLE",
                            "500",
                            "INTERNAL",
                            "DEADLINE",
                            "TIMEOUT",
                            "CONNECTION",
                            "WINERROR 10060",
                        ]
                    )

                    if attempt < 2:

                        if temporary_error:
                            wait_time = 5 * (
                                attempt + 1
                            )
                        else:
                            wait_time = 3 * (
                                attempt + 1
                            )

                        print(
                            f"Retrying in "
                            f"{wait_time} seconds..."
                        )

                        time.sleep(
                            wait_time
                        )

            print(
                "Switching to next model..."
            )

        if last_error:
            raise last_error

        raise RuntimeError(
            "Gemini extraction failed."
        )

    # ==========================================================
    # MISSING VALUE NORMALIZATION
    # ==========================================================

    @classmethod
    def _normalize_missing(
        cls,
        value: Any,
    ) -> Optional[str]:
        """
        Convert common Gemini missing-value representations
        into Python None.
        """

        if value is None:
            return None

        if isinstance(value, bool):
            return str(value)

        text = str(
            value
        ).strip()

        if text.upper() in cls.MISSING_VALUES:
            return None

        return text

    # ==========================================================
    # TEXT NORMALIZATION
    # ==========================================================

    @staticmethod
    def _clean_multiline(
        value: Any,
    ) -> Optional[str]:
        """
        Preserve multiline values while removing accidental
        blank lines and surrounding whitespace.

        Does NOT uppercase the value.
        """

        if value is None:
            return None

        value = str(
            value
        )

        value = value.replace(
            "\r\n",
            "\n",
        )

        value = value.replace(
            "\r",
            "\n",
        )

        lines = []

        for line in value.split("\n"):

            line = line.strip()

            if line:
                lines.append(line)

        if not lines:
            return None

        cleaned = "\n".join(
            lines
        )

        if cleaned.upper() in GeminiService.MISSING_VALUES:
            return None

        return cleaned

    # ==========================================================
    # HEADER EXTRACTION
    # ==========================================================

    def extract_header(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """
        Extract complete shipment/header information using Gemini.
        """

        prompt = load_prompt(
            "header_prompt.txt"
        )

        result = self._generate(
            prompt,
            text,
        )

        if not isinstance(
            result,
            dict,
        ):

            return {
                field:
                    [] if field == "also_notify"
                    else None
                for field in self.HEADER_FIELDS
            }

        normalized = {}

        for field in self.HEADER_FIELDS:

            value = result.get(
                field
            )

            # --------------------------------------------------
            # ALSO NOTIFY
            # --------------------------------------------------

            if field == "also_notify":

                if isinstance(
                    value,
                    list,
                ):

                    notify_list = []

                    for item in value:

                        cleaned = self._clean_multiline(
                            self._normalize_missing(
                                item
                            )
                        )

                        if cleaned:
                            notify_list.append(
                                cleaned
                            )

                    normalized[field] = notify_list

                elif value is None:

                    normalized[field] = []

                else:

                    cleaned = self._clean_multiline(
                        self._normalize_missing(
                            value
                        )
                    )

                    normalized[field] = (
                        [cleaned]
                        if cleaned
                        else []
                    )

                continue

            # --------------------------------------------------
            # Normal field
            # --------------------------------------------------

            value = self._normalize_missing(
                value
            )

            value = self._clean_multiline(
                value
            )

            normalized[field] = value

        # ======================================================
        # SAFE NORMALIZATION
        # ======================================================

        # Voyage:
        # 533 E -> 533E
        if normalized.get("voyage"):

            normalized["voyage"] = re.sub(
                r"\s+",
                "",
                normalized["voyage"],
            ).upper()

        # B/L number
        if normalized.get(
            "bill_of_lading_number"
        ):

            normalized[
                "bill_of_lading_number"
            ] = re.sub(
                r"\s+",
                "",
                normalized[
                    "bill_of_lading_number"
                ].upper(),
            )

        # Booking number
        if normalized.get(
            "booking_number"
        ):

            normalized[
                "booking_number"
            ] = re.sub(
                r"\s+",
                "",
                normalized[
                    "booking_number"
                ].upper(),
            )

        # Freight
        if normalized.get(
            "freight"
        ):

            normalized[
                "freight"
            ] = normalized[
                "freight"
            ].strip().upper()

        # ======================================================
        # IMPORTANT SAFETY CHECK
        # ======================================================
        #
        # Gemini may incorrectly copy the B/L number,
        # page information, or B/L labels into
        # carrier_reference.
        #
        # Only remove the value when it is clearly
        # contaminated by the B/L number or page text.
        #

        carrier_reference = normalized.get(
            "carrier_reference"
        )

        bill_of_lading_number = normalized.get(
            "bill_of_lading_number"
        )

        if carrier_reference:

            carrier_ref_clean = re.sub(
                r"\s+",
                "",
                carrier_reference
            ).upper()

            bl_clean = re.sub(
                r"\s+",
                "",
                bill_of_lading_number or ""
            ).upper()

            # --------------------------------------------------
            # Case 1:
            # Carrier reference is exactly the B/L number
            # --------------------------------------------------

            if (
                bl_clean
                and
                carrier_ref_clean == bl_clean
            ):

                normalized[
                    "carrier_reference"
                ] = None

            # --------------------------------------------------
            # Case 2:
            # Carrier reference contains the B/L number
            # together with obvious page/B/L label text.
            #
            # Example:
            # B/L-No.: HLCUSEL250866591 2 / 3
            # --------------------------------------------------

            elif (
                bl_clean
                and
                bl_clean in carrier_ref_clean
                and
                (
                    "PAGE" in carrier_ref_clean
                    or
                    "BL-NO" in carrier_ref_clean
                    or
                    "BLNO" in carrier_ref_clean
                    or
                    "B/L" in carrier_reference.upper()
                    or
                    "BILL OF LADING" in carrier_reference.upper()
                )
            ):

                normalized[
                    "carrier_reference"
                ] = None

        # ======================================================
        # DEBUG
        # ======================================================

        print(
            "\n========== HEADER =========="
        )

        for field in self.HEADER_FIELDS:

            print(
                f"{field} :",
                normalized.get(
                    field
                ),
            )

        print(
            "============================"
        )

        return normalized

    # ==========================================================
    # CONTAINER EXTRACTION
    # ==========================================================

    def extract_containers(
        self,
        text: str,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract every physical container from the complete
        Bill of Lading using Gemini.

        IMPORTANT:
            Duplicate containers are NOT removed here.

        They must reach the validation stage so that validation
        can report the duplicate instead of silently hiding it.
        """

        prompt = load_prompt(
            "container_prompt.txt"
        )

        result = self._generate(
            prompt,
            text,
        )

        if not isinstance(
            result,
            dict,
        ):

            return {
                "containers": []
            }

        containers = result.get(
            "containers",
            [],
        )

        if not isinstance(
            containers,
            list,
        ):

            return {
                "containers": []
            }

        normalized_containers = []

        # ======================================================
        # IMPORTANT
        # ======================================================
        #
        # DO NOT deduplicate here.
        #
        # Validation needs to see every extracted record.
        # ======================================================

        for container in containers:

            if not isinstance(
                container,
                dict,
            ):
                continue

            normalized = {
                "container_number": None,
                "seal_number": None,
                "size": None,
                "cartons": None,
                "weight_kg": None,
                "cbm": None,
            }

            # ==================================================
            # CONTAINER NUMBER
            # ==================================================

            value = container.get(
                "container_number"
            )

            value = self._normalize_missing(
                value
            )

            if value:

                value = re.sub(
                    r"\s+",
                    "",
                    value.upper(),
                )

                if value:

                    normalized[
                        "container_number"
                    ] = value

            # ==================================================
            # SEAL NUMBER
            # ==================================================

            value = container.get(
                "seal_number"
            )

            value = self._normalize_missing(
                value
            )

            if value:

                value = re.sub(
                    r"\s+",
                    "",
                    value.upper(),
                )

                if value:

                    normalized[
                        "seal_number"
                    ] = value

            # ==================================================
            # SIZE
            # ==================================================

            value = self._normalize_missing(
                container.get(
                    "size"
                )
            )

            if value:

                normalized[
                    "size"
                ] = value.strip().upper()

            # ==================================================
            # CARTONS
            # ==================================================

            normalized[
                "cartons"
            ] = self._normalize_nonnegative_number(
                container.get(
                    "cartons"
                )
            )

            # ==================================================
            # WEIGHT
            # ==================================================

            normalized[
                "weight_kg"
            ] = self._normalize_nonnegative_number(
                container.get(
                    "weight_kg"
                )
            )

            # ==================================================
            # CBM
            # ==================================================

            normalized[
                "cbm"
            ] = self._normalize_nonnegative_number(
                container.get(
                    "cbm"
                )
            )

            # ==================================================
            # STORE RECORD
            # ==================================================

            normalized_containers.append(
                normalized
            )

        # ======================================================
        # DEBUG
        # ======================================================

        print(
            "\n========== CONTAINERS =========="
        )

        print(
            "Total Containers Extracted :",
            len(
                normalized_containers
            ),
        )

        for index, container in enumerate(
            normalized_containers,
            start=1,
        ):

            print(
                f"\nContainer {index}:"
            )

            print(
                "  Number :",
                container[
                    "container_number"
                ],
            )

            print(
                "  Seal   :",
                container[
                    "seal_number"
                ],
            )

            print(
                "  Size   :",
                container[
                    "size"
                ],
            )

            print(
                "  Cartons:",
                container[
                    "cartons"
                ],
            )

            print(
                "  Weight :",
                container[
                    "weight_kg"
                ],
            )

            print(
                "  CBM    :",
                container[
                    "cbm"
                ],
            )

        print(
            "================================"
        )

        return {
            "containers":
                normalized_containers
        }

    # ==========================================================
    # NUMBER NORMALIZATION
    # ==========================================================

    @classmethod
    def _normalize_nonnegative_number(
        cls,
        value: Any,
    ) -> Optional[Any]:

        number = cls._parse_number(
            value
        )

        if number is None:
            return None

        if number < 0:
            return None

        if number.is_integer():
            return int(number)

        return number

    # ==========================================================
    # NUMBER PARSER
    # ==========================================================

    @staticmethod
    def _parse_number(
        value: Any,
    ) -> Optional[float]:
        """
        Convert OCR/Gemini numerical values safely.

        Examples:

            28870
            28870.000
            28,870.000
            1,400
            9705 CARTONS
            32.40 CBM
        """

        if value is None:
            return None

        if isinstance(
            value,
            bool,
        ):
            return None

        if isinstance(
            value,
            int,
        ):
            return float(value)

        if isinstance(
            value,
            float,
        ):

            if value != value:
                return None

            return value

        text = str(
            value
        ).strip()

        if not text:
            return None

        text = text.replace(
            "\u00a0",
            " ",
        )

        text = text.replace(
            " ",
            "",
        )

        # Keep only number-related characters.
        text = re.sub(
            r"[^0-9,.\-+]",
            "",
            text,
        )

        if not text:
            return None

        # ------------------------------------------------------
        # Both comma and decimal point
        # ------------------------------------------------------

        if "," in text and "." in text:

            last_comma = text.rfind(",")
            last_dot = text.rfind(".")

            # Example:
            # 28,870.000
            if last_dot > last_comma:

                text = text.replace(
                    ",",
                    "",
                )

            # Example:
            # 28.870,000
            else:

                text = text.replace(
                    ".",
                    "",
                )

                text = text.replace(
                    ",",
                    ".",
                )

        # ------------------------------------------------------
        # Only comma
        # ------------------------------------------------------

        elif "," in text:

            parts = text.split(",")

            # Example:
            # 28870,000
            if (
                len(parts) == 2
                and len(parts[1]) == 3
                and len(parts[0]) >= 4
            ):

                text = (
                    parts[0]
                    + "."
                    + parts[1]
                )

            # Example:
            # 1,400
            # 28,000
            elif (
                len(parts) > 1
                and all(
                    len(part) == 3
                    for part in parts[1:]
                )
            ):

                text = text.replace(
                    ",",
                    "",
                )

            else:

                text = text.replace(
                    ",",
                    ".",
                )

        # ------------------------------------------------------
        # Only decimal point
        # ------------------------------------------------------

        elif "." in text:

            parts = text.split(".")

            # Example:
            # 1.234.567
            if len(parts) > 2:

                if all(
                    len(part) == 3
                    for part in parts[1:]
                ):

                    text = text.replace(
                        ".",
                        "",
                    )

        try:

            return float(
                text
            )

        except (
            ValueError,
            TypeError,
        ):

            return None

    # ==========================================================
    # DOCUMENT TOTAL EXTRACTION
    # ==========================================================

    def extract_document_totals(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """
        Extract shipment-level totals that are explicitly printed
        in the Bill of Lading.

        IMPORTANT:
            - This method does NOT use Gemini.
            - It does NOT calculate totals from containers.
            - It only reads values explicitly printed in the BL.
            - It supports Hapag-Lloyd aggregate tables.
            - It supports Maersk single-container wording.
            - Missing values remain None.

        The patterns are intentionally additive: the existing Hapag
        patterns are preserved, and Maersk-specific patterns are added
        without changing container extraction or validation.
        """

        normalized = {
            "total_containers": None,
            "total_cartons": None,
            "total_weight": None,
            "total_cbm": None,
        }

        if not text or not text.strip():
            return normalized

        document_text = (
            text
            .replace("\r\n", "\n")
            .replace("\r", "\n")
        )

        # ======================================================
        # TOTAL CONTAINERS
        # ======================================================

        container_patterns = [

            # --------------------------------------------------
            # MAERSK
            # Example:
            # 1 Container Said to Contain 1388 CARTONS
            # --------------------------------------------------
            r"\b(\d[\d,]*)\s+"
            r"CONTAINER(?:S)?\s+SAID\s+TO\s+CONTAIN\b",

            # --------------------------------------------------
            # HAPAG-LLOYD
            # Example: 20 CNTRS
            # --------------------------------------------------
            r"\b(\d[\d,]*)\s*CNTRS?\b",

            # --------------------------------------------------
            # Generic explicit total
            # --------------------------------------------------
            r"\bTOTAL\s+CONTAINERS?\s*[:\-]?\s*([\d,]+)",

            # --------------------------------------------------
            # TOTAL QTY: 20 CONTAINERS
            # --------------------------------------------------
            r"\bTOTAL\s+Q(?:'|\u2019)?TY\s*[:\-]?\s*"
            r"([\d,]+)\s*(?:CNTRS?|CONTAINERS?)\b",
        ]

        normalized["total_containers"] = (
            self._find_first_explicit_number(
                document_text,
                container_patterns,
            )
        )

        # ======================================================
        # TOTAL CARTONS
        # ======================================================

        carton_unit = r"(?:CARTONS?|CTNS?|CTN|CIN)"

        carton_patterns = [

            # --------------------------------------------------
            # MAERSK
            # Example:
            # 1 Container Said to Contain 1388 CARTONS
            # --------------------------------------------------
            r"\b\d[\d,]*\s+"
            r"CONTAINER(?:S)?\s+SAID\s+TO\s+CONTAIN\s+"
            rf"([\d,]+(?:\.\d+)?)\s*{carton_unit}\b",

            # --------------------------------------------------
            # HAPAG-LLOYD explicit total
            # --------------------------------------------------
            r"\bTOTAL\s+Q(?:'|\u2019)?TY\s*[:\-]?\s*"
            rf"([\d,]+(?:\.\d+)?)\s*{carton_unit}\b",

            r"\bTOTAL\s+CARTONS?\s*[:\-]?\s*"
            r"([\d,]+(?:\.\d+)?)",

            # --------------------------------------------------
            # Generic explicit total containing carton unit
            # --------------------------------------------------
            r"\bTOTAL\b[^\n]{0,100}?"
            rf"([\d,]+(?:\.\d+)?)\s*{carton_unit}\b",

            # --------------------------------------------------
            # Hapag-Lloyd aggregate table
            # Example:
            # 7 CNTRS
            # MARKS & NOS: 9705 CARTONS 203805.000 280.000
            # KGM CBM
            # --------------------------------------------------
            r"\b\d[\d,]*\s*CNTRS?\b[\s\S]{0,200}?"
            r"\bMARKS\s*&\s*NOS\b[^\n]*?"
            rf"([\d,]+(?:\.\d+)?)\s*{carton_unit}\b",
        ]

        normalized["total_cartons"] = (
            self._find_first_explicit_number(
                document_text,
                carton_patterns,
            )
        )

        # ======================================================
        # TOTAL GROSS WEIGHT
        # ======================================================

        # total_weight means shipment GROSS weight.
        # TOTAL N.W. is intentionally NOT used.

        weight_patterns = [

            # --------------------------------------------------
            # MAERSK
            # Example OCR:
            # 1 Container Said to Contain 1388 CARTONS
            # FROZEN FISH
            # ...
            # 28870.000 KGS
            #
            # Read a weight only from the area belonging to the
            # explicit single-container statement.
            # --------------------------------------------------
            r"\b\d[\d,]*\s+"
            r"CONTAINER(?:S)?\s+SAID\s+TO\s+CONTAIN\b"
            r"[\s\S]{0,350}?"
            r"([\d,]+(?:\.\d+)?)\s*(?:KGM|KGS?|KG)\b",

            # --------------------------------------------------
            # MAERSK row fallback
            # Example:
            # 1388 CARTONS 28870.000KGS
            # --------------------------------------------------
            rf"\b[\d,]+(?:\.\d+)?\s*{carton_unit}\s+"
            r"([\d,]+(?:\.\d+)?)\s*(?:KGM|KGS?|KG)\b",

            # --------------------------------------------------
            # HAPAG-LLOYD explicit total
            # --------------------------------------------------
            r"\bTOTAL\s+G\.?\s*W\.?\s*[:\-]?\s*"
            r"([\d,]+(?:\.\d+)?)\s*(?:KGM|KGS?|KG)\b",

            r"\bTOTAL\s+GROSS\s+WEIGHT\s*[:\-]?\s*"
            r"([\d,]+(?:\.\d+)?)\s*(?:KGM|KGS?|KG)\b",

            r"\bTOTAL\s+WEIGHT\s*[:\-]?\s*"
            r"([\d,]+(?:\.\d+)?)\s*(?:KGM|KGS?|KG)\b",

            # --------------------------------------------------
            # Generic explicit TOTAL line containing gross weight
            # --------------------------------------------------
            r"\bTOTAL\b[^\n]{0,100}?"
            r"([\d,]+(?:\.\d+)?)\s*(?:KGM|KGS?|KG)\b",

            # --------------------------------------------------
            # Hapag-Lloyd aggregate table
            # --------------------------------------------------
            # Example OCR:
            #
            # 20 CNTRS
            # MARKS & NOS: 28000 CARTONS 582400.000 800.000
            # N/M FROZEN FISH KGM CBM
            #
            # Capture 582400 (the first number after CARTONS).
            #
            # IMPORTANT:
            # Do not require KGM CBM to be immediately after
            # the measurement value because OCR may place
            # description text between the numbers and KGM CBM.
            # --------------------------------------------------
            r"\b\d[\d,]*\s*CNTRS?\b[\s\S]{0,200}?"
            r"\bMARKS\s*&\s*NOS\b[^\n]*?"
            rf"[\d,]+(?:\.\d+)?\s*{carton_unit}\s+"
            r"([\d,]+(?:\.\d+)?)",
        ]

        normalized["total_weight"] = (
            self._find_first_explicit_number(
                document_text,
                weight_patterns,
            )
        )

        # ======================================================
        # TOTAL CBM
        # ======================================================

        cbm_patterns = [

            # Hapag / generic explicit measurement
            r"\bTOTAL\s+MEASUREMENT\s*[:\-]?\s*"
            r"([\d,]+(?:\.\d+)?)\s*CBM\b",

            r"\bTOTAL\s+CBM\s*[:\-]?\s*"
            r"([\d,]+(?:\.\d+)?)",

            r"\bTOTAL\b[^\n]{0,100}?"
            r"([\d,]+(?:\.\d+)?)\s*CBM\b",

            # Hapag-Lloyd aggregate table
            r"\b\d[\d,]*\s*CNTRS?\b[\s\S]{0,500}?"
            r"\bMARKS\s*&\s*NOS\b[\s\S]{0,250}?"
            rf"[\d,]+(?:\.\d+)?\s*{carton_unit}\s+"
            r"[\d,]+(?:\.\d+)?\s+"
            r"([\d,]+(?:\.\d+)?)\s*[\s\S]{0,100}?\bKGM\s+CBM\b",

            # Hapag-Lloyd repeated aggregate row
            rf"\b[\d,]+(?:\.\d+)?\s*{carton_unit}\s+"
            r"[\d,]+(?:\.\d+)?\s+"
            r"([\d,]+(?:\.\d+)?)\s*(?:\n|\s)*\bKGM\s+CBM\b",
        ]

        normalized["total_cbm"] = (
            self._find_first_explicit_number(
                document_text,
                cbm_patterns,
            )
        )

        # ======================================================
        # DEBUG
        # ======================================================

        print(
            "\n========== DOCUMENT TOTALS =========="
        )

        print(
            "total_containers :",
            normalized["total_containers"],
        )

        print(
            "total_cartons    :",
            normalized["total_cartons"],
        )

        print(
            "total_weight     :",
            normalized["total_weight"],
        )

        print(
            "total_cbm        :",
            normalized["total_cbm"],
        )

        print(
            "======================================"
        )

        return normalized

    # ==========================================================
    # EXPLICIT TOTAL NUMBER FINDER
    # ==========================================================

    @classmethod
    def _find_first_explicit_number(
        cls,
        text: str,
        patterns: List[str],
    ) -> Optional[Any]:
        """
        Search for the first explicitly labelled document total.

        No calculation is performed here.
        """

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            value = cls._normalize_nonnegative_number(
                match.group(1)
            )

            if value is not None:
                return value

        return None

    # ==========================================================
    # CONTAINER VALIDATION
    # ==========================================================

    def validate_containers(
        self,
        containers_result,
        summary=None,
    ):
        """
        Validate extracted containers.

        IMPORTANT:

        Missing optional document fields do NOT automatically
        make the complete extraction FAIL.

        Example:

            Maersk document has no CBM.

        Correct:

            cbm = None
            cbm validation = UNAVAILABLE
            overall status = PASS

        A validation FAIL means that something explicitly
        contradictory or structurally invalid was detected.
        """

        print(
            "\n========== CONTAINER VALIDATION =========="
        )

        # ======================================================
        # Safety
        # ======================================================

        if not isinstance(
            containers_result,
            dict,
        ):

            containers_result = {
                "containers": []
            }

        containers = containers_result.get(
            "containers",
            [],
        )

        if not isinstance(
            containers,
            list,
        ):

            containers = []

        if not isinstance(
            summary,
            dict,
        ):

            summary = {}

        # ======================================================
        # Storage
        # ======================================================

        validated = []

        seen_numbers = set()

        duplicate_containers = []

        invalid_container_numbers = []

        missing_fields = []

        # ======================================================
        # Process containers
        # ======================================================

        for index, container in enumerate(
            containers,
            start=1,
        ):

            if not isinstance(
                container,
                dict,
            ):
                continue

            container_number = self._normalize_identifier(
                container.get(
                    "container_number"
                )
            )

            seal_number = self._normalize_identifier(
                container.get(
                    "seal_number"
                )
            )

            size = self._normalize_missing(
                container.get(
                    "size"
                )
            )

            if size:

                size = size.strip().upper()

            cartons = self._normalize_nonnegative_number(
                container.get(
                    "cartons"
                )
            )

            weight_kg = self._normalize_nonnegative_number(
                container.get(
                    "weight_kg"
                )
            )

            cbm = self._normalize_nonnegative_number(
                container.get(
                    "cbm"
                )
            )

            # ==================================================
            # Container number check
            # ==================================================

            if not container_number:

                invalid_container_numbers.append(
                    {
                        "index": index,
                        "container_number": None,
                        "reason":
                            "Missing container number",
                    }
                )

            elif not re.fullmatch(
                r"[A-Z]{4}\d{7}",
                container_number,
            ):

                # WARNING ONLY.
                #
                # Do not automatically fail the whole document.
                invalid_container_numbers.append(
                    {
                        "index": index,
                        "container_number":
                            container_number,
                        "reason":
                            "Does not match standard 4-letter + 7-digit format",
                    }
                )

            # ==================================================
            # Duplicate detection
            # ==================================================

            # IMPORTANT:
            # Duplicates are detected HERE.
            #
            # They were deliberately NOT removed during extraction.

            if container_number:

                if container_number in seen_numbers:

                    duplicate_containers.append(
                        container_number
                    )

                else:

                    seen_numbers.add(
                        container_number
                    )

            # ==================================================
            # Missing fields
            # ==================================================

            field_values = {
                "container_number":
                    container_number,

                "seal_number":
                    seal_number,

                "size":
                    size,

                "cartons":
                    cartons,

                "weight_kg":
                    weight_kg,

                "cbm":
                    cbm,
            }

            for field, value in field_values.items():

                if value is None:

                    missing_fields.append(
                        {
                            "container_index":
                                index,

                            "field":
                                field,
                        }
                    )

            # ==================================================
            # Store validated record
            # ==================================================

            validated.append(
                {
                    "container_number":
                        container_number,

                    "seal_number":
                        seal_number,

                    "size":
                        size,

                    "cartons":
                        cartons,

                    "weight_kg":
                        weight_kg,

                    "cbm":
                        cbm,
                }
            )

        # ======================================================
        # PYTHON CALCULATED TOTALS
        #
        # ONLY for validation.
        #
        # NEVER used to fill missing values.
        # ======================================================

        calculated_container_count = len(
            validated
        )

        calculated_cartons = None

        calculated_weight = None

        calculated_cbm = None

        # ------------------------------------------------------
        # Cartons
        # ------------------------------------------------------

        if validated and all(
            c.get("cartons") is not None
            for c in validated
        ):

            calculated_cartons = sum(
                c["cartons"]
                for c in validated
            )

        # ------------------------------------------------------
        # Weight
        # ------------------------------------------------------

        if validated and all(
            c.get("weight_kg") is not None
            for c in validated
        ):

            calculated_weight = sum(
                c["weight_kg"]
                for c in validated
            )

        # ------------------------------------------------------
        # CBM
        # ------------------------------------------------------

        if validated and all(
            c.get("cbm") is not None
            for c in validated
        ):

            calculated_cbm = sum(
                c["cbm"]
                for c in validated
            )

        # ======================================================
        # Compare helper
        # ======================================================

        def compare(
            calculated,
            document_value,
        ):
            """
            Compare Python-calculated totals against
            explicitly printed document totals.
            """

            # No complete individual values available.
            if calculated is None:

                return {
                    "status":
                        "UNAVAILABLE",

                    "calculated":
                        None,

                    "document":
                        document_value,
                }

            # BL did not explicitly provide this total.
            if document_value is None:

                return {
                    "status":
                        "UNAVAILABLE",

                    "calculated":
                        calculated,

                    "document":
                        None,
                }

            try:

                calculated_number = float(
                    calculated
                )

                document_number = float(
                    document_value
                )

                if abs(
                        calculated_number
                        -
                        document_number
                    ) <= 1.0:

                    return {
                        "status":
                            "PASS",

                        "calculated":
                            calculated,

                        "document":
                            document_value,
                    }

                return {
                    "status":
                        "FAIL",

                    "calculated":
                        calculated,

                    "document":
                        document_value,
                }

            except (
                ValueError,
                TypeError,
            ):

                return {
                    "status":
                        "FAIL",

                    "calculated":
                        calculated,

                    "document":
                        document_value,
                }

        # ======================================================
        # Validations
        # ======================================================

        container_count_validation = compare(
            calculated_container_count,
            summary.get(
                "total_containers"
            ),
        )

        cartons_validation = compare(
            calculated_cartons,
            summary.get(
                "total_cartons"
            ),
        )

        weight_validation = compare(
            calculated_weight,
            summary.get(
                "total_weight"
            ),
        )

        cbm_validation = compare(
            calculated_cbm,
            summary.get(
                "total_cbm"
            ),
        )

        # ======================================================
        # Overall status
        #
        # UNAVAILABLE is NOT FAIL.
        # ======================================================

        failed = False

        validation_results = [
            container_count_validation,
            cartons_validation,
            weight_validation,
            cbm_validation,
        ]

        for validation_result in validation_results:

            if validation_result[
                "status"
            ] == "FAIL":

                failed = True

        # Duplicate physical containers are a real problem.
        if duplicate_containers:

            failed = True

        # Missing container numbers are a real structural problem.
        for item in invalid_container_numbers:

            if item[
                "container_number"
            ] is None:

                failed = True

        overall_status = (
            "FAIL"
            if failed
            else "PASS"
        )

        # ======================================================
        # Validation object
        # ======================================================

        validation = {

            "status":
                overall_status,

            "container_count":
                container_count_validation,

            "cartons":
                cartons_validation,

            "weight_kg":
                weight_validation,

            "cbm":
                cbm_validation,

            "duplicate_container_numbers":
                duplicate_containers,

            "invalid_container_numbers":
                invalid_container_numbers,

            "missing_fields":
                missing_fields,

            "calculated_totals": {

                "total_containers":
                    calculated_container_count,

                "total_cartons":
                    calculated_cartons,

                "total_weight":
                    calculated_weight,

                "total_cbm":
                    calculated_cbm,
            },

            "document_totals": {

                "total_containers":
                    summary.get(
                        "total_containers"
                    ),

                "total_cartons":
                    summary.get(
                        "total_cartons"
                    ),

                "total_weight":
                    summary.get(
                        "total_weight"
                    ),

                "total_cbm":
                    summary.get(
                        "total_cbm"
                    ),
            },
        }

        # ======================================================
        # DEBUG
        # ======================================================

        print(
            "Overall Status :",
            overall_status,
        )

        print(
            "Container Count:",
            container_count_validation[
                "status"
            ],
        )

        print(
            "Cartons        :",
            cartons_validation[
                "status"
            ],
        )

        print(
            "Weight         :",
            weight_validation[
                "status"
            ],
        )

        print(
            "CBM            :",
            cbm_validation[
                "status"
            ],
        )

        print(
            "Duplicates     :",
            duplicate_containers,
        )

        print(
            "Invalid Numbers:",
            invalid_container_numbers,
        )

        print(
            "Missing Fields :",
            missing_fields,
        )

        print(
            "\nCalculated Totals:"
        )

        print(
            "  Containers :",
            calculated_container_count,
        )

        print(
            "  Cartons    :",
            calculated_cartons,
        )

        print(
            "  Weight     :",
            calculated_weight,
        )

        print(
            "  CBM        :",
            calculated_cbm,
        )

        print(
            "\nDocument Totals:"
        )

        print(
            "  Containers :",
            summary.get(
                "total_containers"
            ),
        )

        print(
            "  Cartons    :",
            summary.get(
                "total_cartons"
            ),
        )

        print(
            "  Weight     :",
            summary.get(
                "total_weight"
            ),
        )

        print(
            "  CBM        :",
            summary.get(
                "total_cbm"
            ),
        )

        print(
            "============================================"
        )

        return {

            "containers":
                validated,

            "validation":
                validation,
        }

    # ==========================================================
    # IDENTIFIER NORMALIZATION
    # ==========================================================

    @staticmethod
    def _normalize_identifier(
        value: Any,
    ) -> Optional[str]:
        """
        Normalize identifiers such as:

            HLBU 4821057
            HLBU4821057

        into:

            HLBU4821057

        This only removes whitespace.
        It does NOT invent characters.
        """

        if value is None:
            return None

        text = str(
            value
        ).strip()

        if not text:
            return None

        if text.upper() in GeminiService.MISSING_VALUES:
            return None

        text = re.sub(
            r"\s+",
            "",
            text.upper(),
        )

        return text or None