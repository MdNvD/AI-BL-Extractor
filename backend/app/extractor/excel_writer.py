from openpyxl import Workbook
from openpyxl.styles import (
    Font,
    PatternFill,
    Border,
    Side,
    Alignment
)
from openpyxl.utils import get_column_letter


class ExcelExporter:

    def __init__(self):

        self.header_fill = PatternFill(
            fill_type="solid",
            start_color="1F4E78",
            end_color="1F4E78"
        )

        self.header_font = Font(
            bold=True,
            color="FFFFFF"
        )

        self.thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin")
        )

    def style_sheet(self, ws):

        # Style first row
        for cell in ws[1]:
            cell.fill = self.header_fill
            cell.font = self.header_font
            cell.alignment = Alignment(
                horizontal="center",
                vertical="center"
            )
            cell.border = self.thin_border

        # Style remaining rows
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.border = self.thin_border
                cell.alignment = Alignment(
                    vertical="top",
                    wrap_text=True
                )

        # Auto width
        for column in ws.columns:

            max_length = 0
            column_letter = get_column_letter(column[0].column)

            for cell in column:
                try:
                    if cell.value:
                        max_length = max(
                            max_length,
                            len(str(cell.value))
                        )
                except:
                    pass

            ws.column_dimensions[column_letter].width = min(max_length + 3, 60)

        # Freeze header
        ws.freeze_panes = "A2"

        # Enable filter
        ws.auto_filter.ref = ws.dimensions

    def export(self, data, output_path):

        wb = Workbook()

        # ==========================
        # HEADER SHEET
        # ==========================

        ws1 = wb.active
        ws1.title = "Header"

        ws1.append(["Field", "Value"])

        for key, value in data["header"].items():
            ws1.append([key.replace("_", " ").title(), value])

        self.style_sheet(ws1)

        # ==========================
        # CONTAINER SHEET
        # ==========================

        ws2 = wb.create_sheet("Containers")

        ws2.append([
            "Container Number",
            "Seal Number",
            "Size",
            "Cartons",
            "Weight (KG)",
            "CBM"
        ])

        for container in data["containers"]["containers"]:

            ws2.append([
                container["container_number"],
                container["seal_number"],
                container["size"],
                container["cartons"],
                container["weight_kg"],
                container["cbm"]
            ])

        self.style_sheet(ws2)

        # ==========================
        # SUMMARY SHEET
        # ==========================

        ws3 = wb.create_sheet("Summary")

        ws3.append(["Field", "Value"])

        for key, value in data["summary"].items():
            ws3.append([key.replace("_", " ").title(), value])

        self.style_sheet(ws3)

        wb.save(output_path)