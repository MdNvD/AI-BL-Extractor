from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.config import UPLOAD_DIR
from app.extractor.text_extractor import TextExtractor
from app.extractor.excel_writer import ExcelExporter
from app.services.gemini_service import GeminiService


router = APIRouter(
    tags=["Bill of Lading"]
)


# ======================================================
# Bill of Lading Extraction
# ======================================================

@router.get(
    "/bl-extract/{filename}"
)
def extract_bill_of_lading(
    filename: str
):

    pdf_path = (
        UPLOAD_DIR /
        filename
    )

    # ==================================================
    # File Validation
    # ==================================================

    print(
        "\n========== FILE DEBUG =========="
    )

    print(
        "UPLOAD_DIR :",
        UPLOAD_DIR
    )

    print(
        "Filename   :",
        filename
    )

    print(
        "PDF Path   :",
        pdf_path
    )

    print(
        "Exists     :",
        pdf_path.exists()
    )

    print(
        "================================\n"
    )

    if not pdf_path.exists():

        raise HTTPException(
            status_code=404,
            detail="PDF not found."
        )

    if pdf_path.suffix.lower() != ".pdf":

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    # ==================================================
    # PDF / OCR Extraction
    # ==================================================

    try:

        extractor = TextExtractor(
            str(pdf_path)
        )

        pages = extractor.extract()

    except Exception as e:

        print(
            "Document extraction failed:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to extract text "
                "from PDF."
            )
        )

    print(
        f"Total Pages Extracted : "
        f"{len(pages)}"
    )

    if not pages:

        raise HTTPException(
            status_code=422,
            detail=(
                "No pages could be "
                "extracted from the PDF."
            )
        )

    # ==================================================
    # Combine ALL Pages
    # ==================================================

    document_parts = []

    for page in pages:

        page_number = page.get(
            "page"
        )

        page_text = page.get(
            "text",
            ""
        )

        document_parts.append(
            f"""
==================================================
PAGE {page_number}
==================================================

{page_text}
"""
        )

    document_text = "\n".join(
        document_parts
    )

    # ==================================================
    # Document Information
    # ==================================================

    print(
        "\n========== DOCUMENT INFORMATION =========="
    )

    print(
        "Total pages :",
        len(pages)
    )

    print(
        "Combined document characters :",
        len(document_text)
    )

    print(
        "=========================================="
    )

    # ==================================================
    # Page Debug
    # ==================================================

    for page in pages:

        print(
            f"\n========== PAGE "
            f"{page['page']} PREVIEW =========="
        )

        print(
            page.get(
                "text",
                ""
            )[:1500]
        )

    # ==================================================
    # Gemini
    # ==================================================

    gemini = GeminiService()

    print(
        "\n========== GEMINI EXTRACTION =========="
    )

    try:

        # ----------------------------------------------
        # Header
        # ----------------------------------------------

        header = gemini.extract_header(
            document_text
        )

        # ----------------------------------------------
        # Containers
        # ----------------------------------------------

        containers = (
            gemini.extract_containers(
                document_text
            )
        )

        # ----------------------------------------------
        # Document totals
        #
        # Extract document-level totals from the
        # complete document text.
        # ----------------------------------------------

        summary = (
            gemini.extract_document_totals(
                document_text
            )
        )

        # ----------------------------------------------
        # Local validation
        # ----------------------------------------------

        validated_containers = (
            gemini.validate_containers(
                containers,
                summary
            )
        )

    except Exception as e:

        print(
            "\n========== GEMINI ERROR =========="
        )

        print(
            e
        )

        print(
            "=================================="
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "AI extraction service is "
                "temporarily unavailable."
            )
        )

    # ==================================================
    # Extract validated containers
    # ==================================================

    container_list = (
        validated_containers.get(
            "containers",
            []
        )
    )

    validation = (
        validated_containers.get(
            "validation",
            {}
        )
    )

    # ==================================================
    # Header Debug
    # ==================================================

    print(
        "\n========== HEADER =========="
    )

    for key, value in header.items():

        print(
            f"{key} : {value}"
        )

    print(
        "============================"
    )

    # ==================================================
    # Container Debug
    # ==================================================

    print(
        "\n========== CONTAINERS =========="
    )

    print(
        "Total Containers Extracted :",
        len(container_list)
    )

    for index, container in enumerate(
        container_list,
        start=1
    ):

        print(
            f"\nContainer {index}:"
        )

        print(
            "  Number :",
            container.get(
                "container_number"
            )
        )

        print(
            "  Seal   :",
            container.get(
                "seal_number"
            )
        )

        print(
            "  Size   :",
            container.get(
                "size"
            )
        )

        print(
            "  Cartons:",
            container.get(
                "cartons"
            )
        )

        print(
            "  Weight :",
            container.get(
                "weight_kg"
            )
        )

        print(
            "  CBM    :",
            container.get(
                "cbm"
            )
        )

    print(
        "================================"
    )

    # ==================================================
    # Summary Debug
    # ==================================================

    print(
        "\n========== SUMMARY =========="
    )

    for key, value in summary.items():

        print(
            f"{key} : {value}"
        )

    print(
        "============================="
    )

    # ==================================================
    # Validation Debug
    # ==================================================

    print(
        "\n========== VALIDATION =========="
    )

    print(
        "Status :",
        validation.get(
            "status"
        )
    )

    print(
        "Container Count :",
        validation.get(
            "container_count",
            {}
        ).get(
            "status"
        )
    )

    print(
        "Cartons :",
        validation.get(
            "cartons",
            {}
        ).get(
            "status"
        )
    )

    print(
        "Weight :",
        validation.get(
            "weight_kg",
            {}
        ).get(
            "status"
        )
    )

    print(
        "CBM :",
        validation.get(
            "cbm",
            {}
        ).get(
            "status"
        )
    )

    print(
        "Duplicates :",
        validation.get(
            "duplicate_container_numbers",
            []
        )
    )

    print(
        "Invalid Container Numbers :",
        validation.get(
            "invalid_container_numbers",
            []
        )
    )

    print(
        "Missing Fields :",
        validation.get(
            "missing_fields",
            []
        )
    )

    print(
        "================================"
    )

    # ==================================================
    # Final Result
    # ==================================================

    result = {

        "header":
            header,

        "containers":
            {
                "containers":
                    container_list,

                "validation":
                    validation
            },

        "summary":
            summary
    }

    # ==================================================
    # Save Excel
    # ==================================================

    output_dir = Path(
        "output/excel"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    excel_path = (
        output_dir /
        f"{pdf_path.stem}.xlsx"
    )

    try:

        exporter = ExcelExporter()

        exporter.export(
            result,
            str(excel_path)
        )

    except Exception as e:

        print(
            "Excel export failed:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to create "
                "Excel file."
            )
        )

    print(
        "\nExcel Saved :",
        excel_path
    )

    # ==================================================
    # Response
    # ==================================================

    return {

        "message":
            "Bill of Lading extracted successfully.",

        "excel_file":
            excel_path.name,

        "download_url":
            (
                f"/api/download-excel/"
                f"{excel_path.name}"
            ),

        "data":
            result
    }


# ======================================================
# Excel Download
# ======================================================

@router.get(
    "/download-excel/{filename}"
)
def download_excel(
    filename: str
):

    excel_path = (
        Path("output/excel") /
        filename
    )

    if not excel_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Excel file not found."
        )

    return FileResponse(
        path=excel_path,
        filename=filename,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )