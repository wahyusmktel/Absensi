"""
Layanan Utilitas Ekspor & Impor File Excel (.xlsx) dengan Tampilan UI Rapi dan Bersih.
Menggunakan openpyxl dengan styling header institusional, border, auto-fit kolom, dan format tanggal.
"""

from io import BytesIO
from typing import Any, List
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


class ExcelExportService:
    """
    Generator file Excel dengan styling profesional untuk aplikasi presensi SMP.
    """

    @staticmethod
    def create_styled_workbook(
        title: str,
        school_name: str,
        headers: List[str],
        rows: List[List[Any]],
        sheet_name: str = "Data"
    ) -> BytesIO:
        """
        Membuat workbook Excel dengan header institusional, styling tabel rapi,
        border tipis, zebra striping selang-seling, dan auto lebar kolom.
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = sheet_name

        # Pastikan gridlines aktif
        ws.views.sheetView[0].showGridLines = True

        # Palet Warna PresensiPintar
        navy_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
        zebra_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

        # Font styles
        title_font = Font(name="Segoe UI", size=14, bold=True, color="FFFFFF")
        sub_font = Font(name="Segoe UI", size=10, italic=True, color="E2E8F0")
        header_font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        data_font = Font(name="Segoe UI", size=10, color="1E293B")
        num_font = Font(name="Segoe UI", size=10, color="1E293B")

        # Borders
        thin_border_side = Side(border_style="thin", color="CBD5E1")
        border_all = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)

        num_cols = max(len(headers), 1)

        # 1. Judul & Kop Dokumen
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=num_cols)
        top_cell = ws.cell(row=1, column=1, value=f"PRESENSIPINTAR SMP - {school_name.upper()}")
        top_cell.font = title_font
        top_cell.fill = navy_fill
        top_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 28

        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=num_cols)
        sub_cell = ws.cell(row=2, column=1, value=title.upper())
        sub_cell.font = sub_font
        sub_cell.fill = navy_fill
        sub_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[2].height = 20

        # Baris kosong pemisah
        ws.row_dimensions[3].height = 10

        # 2. Header Tabel Kolom (Baris 4)
        header_row = 4
        ws.row_dimensions[header_row].height = 24
        for col_idx, h_text in enumerate(headers, start=1):
            cell = ws.cell(row=header_row, column=col_idx, value=h_text)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = border_all

        # 3. Baris Data
        curr_row = 5
        for r_idx, r_data in enumerate(rows):
            ws.row_dimensions[curr_row].height = 20
            row_fill = zebra_fill if r_idx % 2 == 1 else white_fill
            for c_idx, val in enumerate(r_data, start=1):
                cell = ws.cell(row=curr_row, column=c_idx, value=val)
                cell.font = data_font
                cell.fill = row_fill
                cell.border = border_all

                # Atur alignment: kolom No atau angka di tengah, teks di kiri
                if c_idx == 1 or isinstance(val, (int, float)):
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center")

            curr_row += 1

        # 4. Auto-fit Lebar Kolom
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            max_len = 0
            for cell in col:
                # Lewati baris 1 & 2 karena merged
                if cell.row in [1, 2, 3]:
                    continue
                v_str = str(cell.value or "")
                if len(v_str) > max_len:
                    max_len = len(v_str)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output
