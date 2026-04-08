from copy import deepcopy
from typing import Any, Optional

DEFAULT_LANG = "en"
SUPPORTED_LANGS = ("en", "id")

LANG_OPTIONS = (
    {"code": "en", "flag": "🇺🇸", "label": "EN"},
    {"code": "id", "flag": "🇮🇩", "label": "ID"},
)

_UI_STRINGS: dict[str, dict[str, Any]] = {
    "en": {
        "page_title": "Document Converter Workspace",
        "menu_converter": "Converter Menu",
        "label_select_converter": "Select converter",
        "label_select_language": "Select language",
        "option_merge_pdf_images": "Merge PDF + Images",
        "option_csv_to_json": "CSV to JSON",
        "option_merge_json": "Merge JSON",
        "header_workspace": "Enterprise Document Hub",
        "header_subtitle": "Secure conversion operations for teams",
        "badge_document_tools": "Document Tools",
        "title_merge_pdf_images": "Merge PDF + Images into One Document",
        "title_csv_to_json": "Convert CSV to JSON",
        "title_merge_json": "Merge Multiple JSON Files into One",
        "desc_merge_pdf_images": "Upload an optional PDF and multiple images. The system trims blank borders and optimizes layout to reduce page count.",
        "desc_csv_to_json": "Upload one CSV file and the system will convert it into a downloadable JSON file.",
        "desc_merge_json": "Upload multiple JSON files, validate matching keys, then merge into a single JSON file.",
        "upload_pdf_optional": "Upload PDF (Optional)",
        "upload_multiple_images": "Upload Multiple Images",
        "selected_images_list": "Selected Images List",
        "selected_count_suffix": "files",
        "drag_reorder_hint": "Drag items to reorder before merging.",
        "empty_selected_images": "No image selected yet.",
        "button_merge_now": "Merge Now",
        "upload_csv": "Upload CSV",
        "csv_output_hint": "Output is a JSON array based on CSV header columns.",
        "button_convert_json": "Convert to JSON",
        "upload_multiple_json": "Upload Multiple JSON Files",
        "json_status_initial": "Select at least 2 JSON files to start key validation.",
        "button_merge_json": "Merge JSON",
        "download_result": "Download Result",
        "download_pdf": "PDF",
        "download_json": "JSON",
        "status_process": "Process Status",
        "quick_guide": "Quick Guide",
        "status_idle": "No process output yet. Run a conversion to see status and download links.",
        "guide_step_1": "Select a mode above, then upload files based on the converter type.",
        "guide_step_2": "For JSON merge, the button is enabled only when all data keys match.",
        "guide_step_3": "Use the download button in the status panel once processing succeeds.",
        "button_close": "Close",
        "alt_fullscreen_preview": "Fullscreen preview",
        "aria_fullscreen_preview": "Fullscreen preview",
        "json_error_array_empty": "{file}: JSON array is empty.",
        "json_error_all_items_object": "{file}: all array items must be JSON objects.",
        "json_error_invalid_root": "{file}: format must be a JSON object or array of objects.",
        "json_error_inconsistent_item_keys": "{file}: item #{index} has inconsistent keys.",
        "json_min_files": "Select at least 2 JSON files to start key validation.",
        "json_error_keys_mismatch_file": "Keys do not match in file {file}.",
        "json_validation_success": "Keys match. Ready to merge {count} JSON files.",
        "json_validation_failed": "JSON key validation failed.",
    },
    "id": {
        "page_title": "Ruang Kerja Konverter Dokumen",
        "menu_converter": "Menu Konverter",
        "label_select_converter": "Pilih konverter",
        "label_select_language": "Pilih bahasa",
        "option_merge_pdf_images": "Gabung PDF + Gambar",
        "option_csv_to_json": "CSV ke JSON",
        "option_merge_json": "Gabung JSON",
        "header_workspace": "Pusat Dokumen Enterprise",
        "header_subtitle": "Operasi konversi aman untuk tim",
        "badge_document_tools": "Alat Dokumen",
        "title_merge_pdf_images": "Gabung PDF + Gambar ke Satu Dokumen",
        "title_csv_to_json": "Konversi CSV Menjadi JSON",
        "title_merge_json": "Gabung Banyak JSON Menjadi Satu",
        "desc_merge_pdf_images": "Unggah PDF opsional dan beberapa gambar. Sistem akan memangkas tepi kosong serta memadatkan tata letak agar jumlah halaman seefisien mungkin.",
        "desc_csv_to_json": "Unggah satu berkas CSV dan sistem akan mengonversinya menjadi berkas JSON siap unduh.",
        "desc_merge_json": "Unggah beberapa berkas JSON, cek kesamaan kunci, lalu gabungkan menjadi satu berkas JSON.",
        "upload_pdf_optional": "Unggah PDF (Opsional)",
        "upload_multiple_images": "Unggah Beberapa Gambar",
        "selected_images_list": "Daftar Gambar Dipilih",
        "selected_count_suffix": "berkas",
        "drag_reorder_hint": "Seret elemen untuk mengubah urutan sebelum proses gabung.",
        "empty_selected_images": "Belum ada gambar dipilih.",
        "button_merge_now": "Gabungkan Sekarang",
        "upload_csv": "Unggah CSV",
        "csv_output_hint": "Output berupa larik JSON sesuai header kolom CSV.",
        "button_convert_json": "Konversi ke JSON",
        "upload_multiple_json": "Unggah Beberapa JSON",
        "json_status_initial": "Pilih minimal 2 berkas JSON untuk mulai cek kunci.",
        "button_merge_json": "Gabungkan JSON",
        "download_result": "Unduh Hasil",
        "download_pdf": "PDF",
        "download_json": "JSON",
        "status_process": "Status Proses",
        "quick_guide": "Panduan Cepat",
        "status_idle": "Belum ada output proses. Jalankan konversi untuk melihat status dan tautan unduh.",
        "guide_step_1": "Pilih mode di atas, lalu unggah berkas sesuai jenis konverter.",
        "guide_step_2": "Untuk gabung JSON, tombol aktif hanya jika semua kunci data cocok.",
        "guide_step_3": "Gunakan tombol unduh di panel status setelah proses berhasil.",
        "button_close": "Tutup",
        "alt_fullscreen_preview": "Pratinjau layar penuh",
        "aria_fullscreen_preview": "Pratinjau layar penuh",
        "json_error_array_empty": "{file}: larik JSON kosong.",
        "json_error_all_items_object": "{file}: semua elemen larik harus berupa objek JSON.",
        "json_error_invalid_root": "{file}: format JSON harus objek atau larik objek.",
        "json_error_inconsistent_item_keys": "{file}: kunci elemen ke-{index} tidak konsisten.",
        "json_min_files": "Pilih minimal 2 berkas JSON untuk mulai cek kunci.",
        "json_error_keys_mismatch_file": "Kunci tidak sama di berkas {file}.",
        "json_validation_success": "Kunci cocok. Siap gabung {count} berkas JSON.",
        "json_validation_failed": "Validasi kunci JSON gagal.",
    },
}

_SERVICE_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "pdf_must_be_pdf": "PDF file must be in .pdf format.",
        "unsupported_image_format": "Unsupported image format: {filename}",
        "no_processable_files": "No processable files were provided.",
        "merge_pdf_images_success": "Successfully merged PDF and images into A4 pages.",
        "csv_file_required": "CSV file is required.",
        "csv_must_be_csv": "File must be in .csv format.",
        "csv_empty": "CSV file is empty.",
        "csv_header_missing": "CSV header row was not found.",
        "csv_convert_success": "Successfully converted CSV to JSON ({rows} rows).",
        "csv_encoding_unsupported": "CSV encoding is not supported. Please use UTF-8.",
        "json_min_two_files": "Please upload at least 2 JSON files to merge.",
        "json_must_be_json": "File must be in .json format: {filename}",
        "json_file_empty": "File is empty: {filename}",
        "json_encoding_unsupported": "Encoding is not supported: {filename}. Please use UTF-8.",
        "json_invalid": "Invalid JSON: {filename}",
        "json_error_array_empty": "{file}: JSON array is empty.",
        "json_error_all_items_object": "{file}: all array items must be JSON objects.",
        "json_error_invalid_root": "{file}: format must be a JSON object or array of objects.",
        "json_error_inconsistent_item_keys": "{file}: item #{index} has inconsistent keys.",
        "json_file_keys_mismatch": "Keys do not match in file {filename}. Make sure all files have identical keys.",
        "json_merge_success": "Successfully merged {count} JSON files ({rows} records).",
        "file_not_found": "File not found",
    },
    "id": {
        "pdf_must_be_pdf": "Berkas PDF harus berformat .pdf",
        "unsupported_image_format": "Format gambar tidak didukung: {filename}",
        "no_processable_files": "Tidak ada berkas yang bisa diproses.",
        "merge_pdf_images_success": "Berhasil menggabungkan PDF dan gambar ke halaman A4.",
        "csv_file_required": "Berkas CSV wajib dipilih.",
        "csv_must_be_csv": "Berkas harus berformat .csv",
        "csv_empty": "Berkas CSV kosong.",
        "csv_header_missing": "Kolom header CSV tidak ditemukan.",
        "csv_convert_success": "Berhasil mengonversi CSV ke JSON ({rows} baris).",
        "csv_encoding_unsupported": "Enkode CSV tidak didukung. Gunakan UTF-8.",
        "json_min_two_files": "Minimal unggah 2 berkas JSON untuk digabungkan.",
        "json_must_be_json": "Berkas harus berformat .json: {filename}",
        "json_file_empty": "Berkas kosong: {filename}",
        "json_encoding_unsupported": "Enkode tidak didukung: {filename}. Gunakan UTF-8.",
        "json_invalid": "JSON tidak valid: {filename}",
        "json_error_array_empty": "{file}: larik JSON kosong.",
        "json_error_all_items_object": "{file}: semua elemen larik harus berupa objek JSON.",
        "json_error_invalid_root": "{file}: format JSON harus objek atau larik objek.",
        "json_error_inconsistent_item_keys": "{file}: kunci elemen ke-{index} tidak konsisten.",
        "json_file_keys_mismatch": "Kunci tidak sama pada berkas {filename}. Pastikan semua berkas memiliki kunci yang identik.",
        "json_merge_success": "Berhasil menggabungkan {count} berkas JSON ({rows} entri).",
        "file_not_found": "Berkas tidak ditemukan",
    },
}


def normalize_lang(lang: Optional[str]) -> str:
    if lang in SUPPORTED_LANGS:
        return lang
    return DEFAULT_LANG


def get_ui_strings(lang: Optional[str]) -> dict[str, Any]:
    current_lang = normalize_lang(lang)
    return deepcopy(_UI_STRINGS[current_lang])


def translate(lang: Optional[str], key: str, **kwargs: Any) -> str:
    current_lang = normalize_lang(lang)
    table = _SERVICE_STRINGS.get(current_lang, _SERVICE_STRINGS[DEFAULT_LANG])
    template = table.get(key, _SERVICE_STRINGS[DEFAULT_LANG].get(key, key))
    return template.format(**kwargs)
