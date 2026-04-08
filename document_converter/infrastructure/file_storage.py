import mimetypes
import uuid
from pathlib import Path
from typing import Any

from fastapi import UploadFile


class FileStorage:
    def __init__(self, upload_dir: Path, output_dir: Path):
        self.upload_dir = upload_dir
        self.output_dir = output_dir
        self.upload_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

    def save_upload(self, upload: UploadFile) -> Path:
        filename = upload.filename or "upload.bin"
        target_path = self.upload_dir / f"{uuid.uuid4()}_{filename}"
        with open(target_path, "wb") as file:
            file.write(upload.file.read())
        return target_path

    def write_output_bytes(self, *, prefix: str, suffix: str, content: bytes) -> str:
        output_name = f"{prefix}_{uuid.uuid4()}{suffix}"
        output_path = self.output_dir / output_name
        with open(output_path, "wb") as file:
            file.write(content)
        return output_name

    def write_output_json(self, *, prefix: str, content: Any) -> str:
        import json

        output_name = f"{prefix}_{uuid.uuid4()}.json"
        output_path = self.output_dir / output_name
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(content, file, ensure_ascii=False, indent=2)
        return output_name

    def output_path(self, filename: str) -> Path:
        return self.output_dir / filename

    def guess_media_type(self, filename: str) -> str:
        return mimetypes.guess_type(filename)[0] or "application/octet-stream"
