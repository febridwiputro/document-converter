from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
TEMPLATE_DIR = BASE_DIR / "templates"


# A4 page size constants for image-to-PDF layout
A4_WIDTH_PX = 1240
A4_HEIGHT_PX = 1754
SIDE_MARGIN = 40
TOP_MARGIN = 110
BOTTOM_MARGIN = 40
IMAGE_GAP = 24
MIN_PAGE_SCALE = 0.45


def ensure_directories() -> None:
    UPLOAD_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
