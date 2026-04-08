from typing import Optional

MODE_MERGE_PDF_IMAGES = "merge_pdf_images"
MODE_CSV_TO_JSON = "csv_to_json"
MODE_MERGE_JSON = "merge_json"

SUPPORTED_MODES = {
    MODE_MERGE_PDF_IMAGES,
    MODE_CSV_TO_JSON,
    MODE_MERGE_JSON,
}


def normalize_mode(mode: Optional[str]) -> str:
    if mode in SUPPORTED_MODES:
        return mode
    return MODE_MERGE_PDF_IMAGES
