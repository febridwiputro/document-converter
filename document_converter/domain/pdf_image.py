import io
from typing import List

from PIL import Image, ImageChops
from pypdf import PdfReader

from document_converter.core import config


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

    available_width = config.A4_WIDTH_PX - (2 * config.SIDE_MARGIN)
    available_height = config.A4_HEIGHT_PX - config.TOP_MARGIN - config.BOTTOM_MARGIN

    index = 0
    while index < len(images):
        end = index
        selected_scale = 1.0

        while end < len(images):
            batch = images[index : end + 1]
            full_width_heights = [
                img.height * (available_width / img.width) for img in batch
            ]
            total_height = sum(full_width_heights) + config.IMAGE_GAP * (len(batch) - 1)
            scale = min(1.0, available_height / total_height)

            if scale >= config.MIN_PAGE_SCALE:
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

        page = Image.new("RGB", (config.A4_WIDTH_PX, config.A4_HEIGHT_PX), "white")
        layout: List[tuple[Image.Image, int, int]] = []
        for img in images[index:end]:
            target_w = max(1, int(available_width * selected_scale))
            target_h = max(1, int((img.height / img.width) * target_w))
            layout.append((img, target_w, target_h))

        content_height = sum(h for _, _, h in layout) + config.IMAGE_GAP * (len(layout) - 1)
        y = config.TOP_MARGIN + max(0, (available_height - content_height) // 2)

        for img, target_w, target_h in layout:
            resized = img.resize((target_w, target_h), Image.LANCZOS)
            x = (config.A4_WIDTH_PX - target_w) // 2
            page.paste(resized, (x, y))
            y += target_h + config.IMAGE_GAP

        pages.append(page)
        index = end

    return pages


def page_image_to_pdf_reader(page_image: Image.Image) -> PdfReader:
    buffer = io.BytesIO()
    page_image.save(buffer, format="PDF", resolution=150.0)
    buffer.seek(0)
    return PdfReader(buffer)
