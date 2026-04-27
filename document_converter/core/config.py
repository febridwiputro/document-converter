from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
TEMPLATE_DIR = BASE_DIR / "templates"


# A4 page size constants for image-to-PDF layout (300 DPI)
A4_WIDTH_PX = 2480
A4_HEIGHT_PX = 3508
SIDE_MARGIN = 80
TOP_MARGIN = 220
BOTTOM_MARGIN = 80
IMAGE_GAP = 48
MIN_PAGE_SCALE = 0.45
PDF_EXPORT_DPI = 300
PDF_JPEG_QUALITY = 95


def ensure_directories() -> None:
    UPLOAD_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
