from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.config import UPLOAD_DIR
from app.extractor.text_extractor import TextExtractor
from app.extractor.excel_writer import ExcelExporter
from app.services.gemini_service import GeminiService

router = APIRouter(tags=["Bill of Lading"])


@router.get("/bl-extract/{filename}")
def extract_bill_of_lading(filename: str):

    pdf_path = UPLOAD_DIR / filename

    print("\n========== FILE DEBUG ==========")
    print("UPLOAD_DIR :", UPLOAD_DIR)
    print("Filename   :", filename)
    print("PDF Path   :", pdf_path)
    print("Exists     :", pdf_path.exists())

    if UPLOAD_DIR.exists():
        print("\nFiles inside upload folder:")
        for f in UPLOAD_DIR.iterdir():
            print(" -", f.name)

    print("================================\n")

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail="PDF not found."
        )

    # -----------------------------------
    # OCR Extraction
    # -----------------------------------

    extractor = TextExtractor(str(pdf_path))
    pages = extractor.extract()

    print(f"Total Pages Extracted : {len(pages)}")

    header_text = pages[0]["text"] if len(pages) > 0 else ""
    container_text = pages[1]["text"] if len(pages) > 1 else ""
    summary_text = pages[2]["text"] if len(pages) > 2 else ""

    print("\n========== PAGE 1 ==========")
    print(header_text[:1000])

    print("\n========== PAGE 2 ==========")
    print(container_text[:1000])

    print("\n========== PAGE 3 ==========")
    print(summary_text[:1000])

    # -----------------------------------
    # Gemini Extraction
    # -----------------------------------

    gemini = GeminiService()

    header = gemini.extract_header(header_text)
    containers = gemini.extract_containers(container_text)
    summary = gemini.extract_summary(summary_text)

    # -----------------------------------
    # Debug Output
    # -----------------------------------

    print("\n========== HEADER ==========")

    for key, value in header.items():
        print(f"{key} : {value}")

    print("============================")

    print("\n========== CONTAINERS ==========")
    print(f"Total Containers Extracted : {len(containers.get('containers', []))}")
    print("===============================")

    print("\n========== SUMMARY ==========")

    for key, value in summary.items():
        print(f"{key} : {value}")

    print("=============================")

    # -----------------------------------
    # Recalculate total containers
    # -----------------------------------

    summary["total_containers"] = len(
        containers.get("containers", [])
    )

    # -----------------------------------
    # Final JSON
    # -----------------------------------

    result = {
        "header": header,
        "containers": containers,
        "summary": summary
    }

    # -----------------------------------
    # Save Excel
    # -----------------------------------

    output_dir = Path("output/excel")
    output_dir.mkdir(parents=True, exist_ok=True)

    excel_path = output_dir / f"{pdf_path.stem}.xlsx"

    exporter = ExcelExporter()
    exporter.export(result, str(excel_path))

    print("\nExcel Saved :", excel_path)

    # -----------------------------------
    # Return Response
    # -----------------------------------

    return {
        "message": "Bill of Lading extracted successfully.",
        "excel_file": excel_path.name,
        "download_url": f"/api/download-excel/{excel_path.name}",
        "data": result
    }


@router.get("/download-excel/{filename}")
def download_excel(filename: str):

    excel_path = Path("output/excel") / filename

    if not excel_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Excel file not found."
        )

    return FileResponse(
        path=excel_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )