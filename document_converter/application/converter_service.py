import csv
import io
import json
from pathlib import Path
from typing import List, Optional, Tuple

from fastapi import UploadFile
from PIL import Image
from pypdf import PdfReader, PdfWriter

from document_converter.application.result import UseCaseResult
from document_converter.core.i18n import translate
from document_converter.core.modes import (
    MODE_CSV_TO_JSON,
    MODE_MERGE_JSON,
    MODE_MERGE_PDF_IMAGES,
)
from document_converter.domain.json_tools import (
    JsonValidationError,
    extract_json_records_and_keys,
)
from document_converter.domain.pdf_image import (
    build_image_pages,
    page_image_to_pdf_reader,
    trim_uniform_border,
)
from document_converter.infrastructure.file_storage import FileStorage


class ConverterService:
    def __init__(self, storage: FileStorage):
        self.storage = storage

    @staticmethod
    def _json_validation_error_message(lang: str, error: JsonValidationError) -> str:
        if error.code == "empty_array":
            return translate(lang, "json_error_array_empty", file=error.source_name)
        if error.code == "non_object_item":
            return translate(lang, "json_error_all_items_object", file=error.source_name)
        if error.code == "invalid_root_type":
            return translate(lang, "json_error_invalid_root", file=error.source_name)
        if error.code == "inconsistent_item_keys":
            return translate(
                lang,
                "json_error_inconsistent_item_keys",
                file=error.source_name,
                index=error.index,
            )
        return str(error)

    async def merge_pdf_images(
        self,
        *,
        lang: str,
        merge_order: Optional[str],
        pdf_file: Optional[UploadFile],
        image_files: List[UploadFile],
    ) -> UseCaseResult:
        try:
            writer = PdfWriter()
            has_content = False

            pdf_path: Optional[Path] = None
            if pdf_file and pdf_file.filename:
                if not pdf_file.filename.lower().endswith(".pdf"):
                    return UseCaseResult(
                        mode=MODE_MERGE_PDF_IMAGES,
                        status_code=400,
                        error=translate(lang, "pdf_must_be_pdf"),
                    )

                pdf_path = self.storage.save_upload(pdf_file)

            allowed_image_ext = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
            saved_image_paths: List[Path] = []

            for image in image_files:
                if not image.filename:
                    continue

                ext = Path(image.filename).suffix.lower()
                if ext not in allowed_image_ext:
                    return UseCaseResult(
                        mode=MODE_MERGE_PDF_IMAGES,
                        status_code=400,
                        error=translate(
                            lang,
                            "unsupported_image_format",
                            filename=image.filename,
                        ),
                    )

                img_path = self.storage.save_upload(image)
                saved_image_paths.append(img_path)

            default_order: List[str] = []
            if pdf_path is not None:
                default_order.append("pdf")
            default_order.extend(["image"] * len(saved_image_paths))

            ordered_tokens = self._resolve_merge_order(
                merge_order=merge_order,
                pdf_exists=pdf_path is not None,
                image_count=len(saved_image_paths),
                default_order=default_order,
            )

            image_cursor = 0
            image_run: List[Path] = []

            def flush_image_run() -> int:
                pages_added = 0
                if not image_run:
                    return pages_added

                prepared_images: List[Image.Image] = []
                for img_path in image_run:
                    with Image.open(img_path) as img:
                        prepared = trim_uniform_border(img)
                        prepared_images.append(prepared.copy())

                image_pages = build_image_pages(prepared_images)
                for page_image in image_pages:
                    image_pdf = page_image_to_pdf_reader(page_image)
                    for page in image_pdf.pages:
                        writer.add_page(page)
                        pages_added += 1
                image_run.clear()
                return pages_added

            for token in ordered_tokens:
                if token == "image":
                    if image_cursor < len(saved_image_paths):
                        image_run.append(saved_image_paths[image_cursor])
                        image_cursor += 1
                    continue

                flushed_pages = flush_image_run()
                if flushed_pages > 0:
                    has_content = True
                if token == "pdf" and pdf_path is not None:
                    reader = PdfReader(str(pdf_path))
                    for page in reader.pages:
                        writer.add_page(page)
                        has_content = True

            flushed_pages = flush_image_run()
            if flushed_pages > 0:
                has_content = True

            # Fallback safety if any image token was missing in merge_order.
            while image_cursor < len(saved_image_paths):
                image_run.append(saved_image_paths[image_cursor])
                image_cursor += 1
            flushed_pages = flush_image_run()
            if flushed_pages > 0:
                has_content = True

            if not has_content and pdf_path is not None:
                reader = PdfReader(str(pdf_path))
                for page in reader.pages:
                    writer.add_page(page)
                    has_content = True

            if not has_content:
                return UseCaseResult(
                    mode=MODE_MERGE_PDF_IMAGES,
                    status_code=400,
                    error=translate(lang, "no_processable_files"),
                )

            output_buffer = io.BytesIO()
            writer.write(output_buffer)
            output_name = self.storage.write_output_bytes(
                prefix="merged",
                suffix=".pdf",
                content=output_buffer.getvalue(),
            )

            return UseCaseResult(
                mode=MODE_MERGE_PDF_IMAGES,
                download=f"/download/{output_name}",
                message=translate(lang, "merge_pdf_images_success"),
            )
        except Exception as exc:  # noqa: BLE001
            return UseCaseResult(
                mode=MODE_MERGE_PDF_IMAGES,
                status_code=500,
                error=str(exc),
            )

    @staticmethod
    def _resolve_merge_order(
        *,
        merge_order: Optional[str],
        pdf_exists: bool,
        image_count: int,
        default_order: List[str],
    ) -> List[str]:
        if not merge_order:
            return default_order

        try:
            parsed = json.loads(merge_order)
        except json.JSONDecodeError:
            return default_order

        if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
            return default_order

        normalized = [item.lower() for item in parsed]
        if any(item not in {"pdf", "image"} for item in normalized):
            return default_order

        expected_pdf_count = 1 if pdf_exists else 0
        if normalized.count("pdf") != expected_pdf_count:
            return default_order
        if normalized.count("image") != image_count:
            return default_order

        return normalized

    async def convert_csv_to_json(
        self,
        *,
        lang: str,
        csv_file: UploadFile,
    ) -> UseCaseResult:
        try:
            if not csv_file.filename:
                return UseCaseResult(
                    mode=MODE_CSV_TO_JSON,
                    status_code=400,
                    error=translate(lang, "csv_file_required"),
                )

            if Path(csv_file.filename).suffix.lower() != ".csv":
                return UseCaseResult(
                    mode=MODE_CSV_TO_JSON,
                    status_code=400,
                    error=translate(lang, "csv_must_be_csv"),
                )

            csv_bytes = await csv_file.read()
            if not csv_bytes:
                return UseCaseResult(
                    mode=MODE_CSV_TO_JSON,
                    status_code=400,
                    error=translate(lang, "csv_empty"),
                )

            csv_text = csv_bytes.decode("utf-8-sig")
            sample = csv_text[:4096]
            csv_stream = io.StringIO(csv_text)

            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                reader = csv.DictReader(csv_stream, dialect=dialect)
            except csv.Error:
                csv_stream.seek(0)
                reader = csv.DictReader(csv_stream)

            if not reader.fieldnames:
                return UseCaseResult(
                    mode=MODE_CSV_TO_JSON,
                    status_code=400,
                    error=translate(lang, "csv_header_missing"),
                )

            rows = list(reader)
            output_name = self.storage.write_output_json(prefix="converted", content=rows)

            return UseCaseResult(
                mode=MODE_CSV_TO_JSON,
                download=f"/download/{output_name}",
                message=translate(lang, "csv_convert_success", rows=len(rows)),
            )
        except UnicodeDecodeError:
            return UseCaseResult(
                mode=MODE_CSV_TO_JSON,
                status_code=400,
                error=translate(lang, "csv_encoding_unsupported"),
            )
        except Exception as exc:  # noqa: BLE001
            return UseCaseResult(
                mode=MODE_CSV_TO_JSON,
                status_code=500,
                error=str(exc),
            )

    async def merge_json_files(
        self,
        *,
        lang: str,
        json_files: List[UploadFile],
    ) -> UseCaseResult:
        try:
            valid_files = [file for file in json_files if file.filename]
            if len(valid_files) < 2:
                return UseCaseResult(
                    mode=MODE_MERGE_JSON,
                    status_code=400,
                    error=translate(lang, "json_min_two_files"),
                )

            merged_records: List[dict] = []
            expected_keys: Optional[Tuple[str, ...]] = None

            for json_file in valid_files:
                suffix = Path(json_file.filename).suffix.lower()
                if suffix != ".json":
                    return UseCaseResult(
                        mode=MODE_MERGE_JSON,
                        status_code=400,
                        error=translate(
                            lang,
                            "json_must_be_json",
                            filename=json_file.filename,
                        ),
                    )

                content = await json_file.read()
                if not content:
                    return UseCaseResult(
                        mode=MODE_MERGE_JSON,
                        status_code=400,
                        error=translate(
                            lang,
                            "json_file_empty",
                            filename=json_file.filename,
                        ),
                    )

                try:
                    parsed = json.loads(content.decode("utf-8-sig"))
                except UnicodeDecodeError:
                    return UseCaseResult(
                        mode=MODE_MERGE_JSON,
                        status_code=400,
                        error=translate(
                            lang,
                            "json_encoding_unsupported",
                            filename=json_file.filename,
                        ),
                    )
                except json.JSONDecodeError:
                    return UseCaseResult(
                        mode=MODE_MERGE_JSON,
                        status_code=400,
                        error=translate(
                            lang,
                            "json_invalid",
                            filename=json_file.filename,
                        ),
                    )

                try:
                    records, keys = extract_json_records_and_keys(
                        parsed,
                        source_name=json_file.filename,
                    )
                except JsonValidationError as exc:
                    return UseCaseResult(
                        mode=MODE_MERGE_JSON,
                        status_code=400,
                        error=self._json_validation_error_message(lang, exc),
                    )

                if expected_keys is None:
                    expected_keys = keys
                elif keys != expected_keys:
                    return UseCaseResult(
                        mode=MODE_MERGE_JSON,
                        status_code=400,
                        error=translate(
                            lang,
                            "json_file_keys_mismatch",
                            filename=json_file.filename,
                        ),
                    )

                merged_records.extend(records)

            output_name = self.storage.write_output_json(
                prefix="merged_json",
                content=merged_records,
            )
            return UseCaseResult(
                mode=MODE_MERGE_JSON,
                download=f"/download/{output_name}",
                message=translate(
                    lang,
                    "json_merge_success",
                    count=len(valid_files),
                    rows=len(merged_records),
                ),
            )
        except Exception as exc:  # noqa: BLE001
            return UseCaseResult(
                mode=MODE_MERGE_JSON,
                status_code=500,
                error=str(exc),
            )
