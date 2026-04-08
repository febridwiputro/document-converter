import io
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from PIL import Image, ImageChops
from pypdf import PdfReader, PdfWriter

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
TEMPLATE_DIR = BASE_DIR / "templates"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="PDF + Images Merger A4")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# A4 size in points for PDF
A4_WIDTH_PT = 595
A4_HEIGHT_PT = 842

# Canvas image size for rendering A4 page
A4_WIDTH_PX = 1240
A4_HEIGHT_PX = 1754
SIDE_MARGIN = 40
TOP_MARGIN = 110
BOTTOM_MARGIN = 40
IMAGE_GAP = 24
MIN_PAGE_SCALE = 0.45


def save_upload(upload: UploadFile, path: Path) -> None:
    with open(path, "wb") as f:
        f.write(upload.file.read())


def trim_uniform_border(img: Image.Image, tolerance: int = 8) -> Image.Image:
    """Crop border kosong dengan warna seragam (umum pada screenshot)."""
    if img.mode != "RGB":
        img = img.convert("RGB")

    bg_color = img.getpixel((0, 0))
    bg = Image.new("RGB", img.size, bg_color)
    diff = ImageChops.difference(img, bg).convert("L")
    mask = diff.point(lambda p: 255 if p > tolerance else 0)
    bbox = mask.getbbox()
    if bbox is None:
        return img
    return img.crop(bbox)


def build_image_pages(images: List[Image.Image]) -> List[Image.Image]:
    """Pack image ke halaman A4 sesedikit mungkin."""
    pages: List[Image.Image] = []
    if not images:
        return pages

    available_width = A4_WIDTH_PX - (2 * SIDE_MARGIN)
    available_height = A4_HEIGHT_PX - TOP_MARGIN - BOTTOM_MARGIN

    index = 0
    while index < len(images):
        end = index
        selected_scale = 1.0

        while end < len(images):
            batch = images[index : end + 1]
            full_width_heights = [
                img.height * (available_width / img.width) for img in batch
            ]
            total_height = sum(full_width_heights) + IMAGE_GAP * (len(batch) - 1)
            scale = min(1.0, available_height / total_height)

            if scale >= MIN_PAGE_SCALE:
                selected_scale = scale
                end += 1
                continue
            break

        if end == index:
            # Jika 1 image saja sudah tinggi, tetap render sendiri di halaman ini.
            single = images[index]
            single_height = single.height * (available_width / single.width)
            selected_scale = min(1.0, available_height / single_height)
            end = index + 1

        page = Image.new("RGB", (A4_WIDTH_PX, A4_HEIGHT_PX), "white")
        layout: List[tuple[Image.Image, int, int]] = []
        for img in images[index:end]:
            target_w = max(1, int(available_width * selected_scale))
            target_h = max(1, int((img.height / img.width) * target_w))
            layout.append((img, target_w, target_h))

        content_height = sum(h for _, _, h in layout) + IMAGE_GAP * (len(layout) - 1)
        y = TOP_MARGIN + max(0, (available_height - content_height) // 2)

        for img, target_w, target_h in layout:
            resized = img.resize((target_w, target_h), Image.LANCZOS)
            x = (A4_WIDTH_PX - target_w) // 2
            page.paste(resized, (x, y))
            y += target_h + IMAGE_GAP

        pages.append(page)
        index = end

    return pages


def page_image_to_pdf_reader(page_image: Image.Image) -> PdfReader:
    buffer = io.BytesIO()
    page_image.save(buffer, format="PDF", resolution=150.0)
    buffer.seek(0)
    return PdfReader(buffer)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "download": None,
            "error": None,
            "message": None,
        },
    )


@app.post("/merge", response_class=HTMLResponse)
async def merge_pdf_images(
    request: Request,
    pdf_file: Optional[UploadFile] = File(None),
    image_files: List[UploadFile] = File(...),
):
    try:
        writer = PdfWriter()
        has_content = False

        # Tambahkan PDF dulu jika ada
        if pdf_file and pdf_file.filename:
            if not pdf_file.filename.lower().endswith(".pdf"):
                return templates.TemplateResponse(
                    "index.html",
                    {
                        "request": request,
                        "download": None,
                        "error": "File PDF harus berformat .pdf",
                        "message": None,
                    },
                    status_code=400,
                )

            pdf_path = UPLOAD_DIR / f"{uuid.uuid4()}_{pdf_file.filename}"
            save_upload(pdf_file, pdf_path)

            reader = PdfReader(str(pdf_path))
            for page in reader.pages:
                writer.add_page(page)
                has_content = True

        # Tambahkan semua image sebagai halaman A4 (dengan packing otomatis)
        allowed_image_ext = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
        saved_image_paths: List[Path] = []

        for image in image_files:
            if not image.filename:
                continue

            ext = Path(image.filename).suffix.lower()
            if ext not in allowed_image_ext:
                return templates.TemplateResponse(
                    "index.html",
                    {
                        "request": request,
                        "download": None,
                        "error": f"Format image tidak didukung: {image.filename}",
                        "message": None,
                    },
                    status_code=400,
                )

            img_path = UPLOAD_DIR / f"{uuid.uuid4()}_{image.filename}"
            save_upload(image, img_path)
            saved_image_paths.append(img_path)

        prepared_images: List[Image.Image] = []
        for img_path in saved_image_paths:
            with Image.open(img_path) as img:
                prepared = trim_uniform_border(img)
                prepared_images.append(prepared.copy())

        image_pages = build_image_pages(prepared_images)
        for page_image in image_pages:
            image_pdf = page_image_to_pdf_reader(page_image)
            for page in image_pdf.pages:
                writer.add_page(page)
                has_content = True

        if not has_content:
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "download": None,
                    "error": "Tidak ada file yang bisa diproses.",
                    "message": None,
                },
                status_code=400,
            )

        output_name = f"merged_{uuid.uuid4()}.pdf"
        output_path = OUTPUT_DIR / output_name

        with open(output_path, "wb") as f:
            writer.write(f)

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "download": f"/download/{output_name}",
                "error": None,
                "message": "Berhasil merge PDF dan image ke halaman A4.",
            },
        )

    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "download": None,
                "error": str(e),
                "message": None,
            },
            status_code=500,
        )


@app.get("/download/{filename}")
async def download(filename: str):
    path = OUTPUT_DIR / filename

    if not path.exists():
        return {"error": "File tidak ditemukan"}

    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename=filename,
    )
