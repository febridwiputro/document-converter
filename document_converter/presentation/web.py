from typing import Optional

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from document_converter.application.converter_service import ConverterService
from document_converter.application.result import UseCaseResult
from document_converter.core import config
from document_converter.core.i18n import (
    DEFAULT_LANG,
    LANG_OPTIONS,
    get_ui_strings,
    normalize_lang,
    translate,
)
from document_converter.core.modes import normalize_mode
from document_converter.infrastructure.file_storage import FileStorage


def render_index(
    *,
    templates: Jinja2Templates,
    request: Request,
    result: UseCaseResult,
    lang: str,
):
    current_lang = normalize_lang(lang)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "lang": current_lang,
            "lang_options": LANG_OPTIONS,
            "i18n": get_ui_strings(current_lang),
            "mode": result.mode,
            "download": result.download,
            "error": result.error,
            "message": result.message,
        },
        status_code=result.status_code,
    )


def create_app() -> FastAPI:
    config.ensure_directories()

    app = FastAPI(title="Document Converter")
    templates = Jinja2Templates(directory=str(config.TEMPLATE_DIR))

    storage = FileStorage(upload_dir=config.UPLOAD_DIR, output_dir=config.OUTPUT_DIR)
    service = ConverterService(storage=storage)

    @app.get("/", response_class=HTMLResponse)
    async def home(
        request: Request,
        mode: Optional[str] = None,
        lang: Optional[str] = None,
    ):
        current_lang = normalize_lang(lang)
        result = UseCaseResult(mode=normalize_mode(mode))
        return render_index(
            templates=templates,
            request=request,
            result=result,
            lang=current_lang,
        )

    @app.post("/merge", response_class=HTMLResponse)
    async def merge_pdf_images(
        request: Request,
        lang: str = Form(DEFAULT_LANG),
        pdf_file: Optional[UploadFile] = File(None),
        image_files: list[UploadFile] = File(...),
    ):
        current_lang = normalize_lang(lang)
        result = await service.merge_pdf_images(
            lang=current_lang,
            pdf_file=pdf_file,
            image_files=image_files,
        )
        return render_index(
            templates=templates,
            request=request,
            result=result,
            lang=current_lang,
        )

    @app.post("/convert-csv", response_class=HTMLResponse)
    async def convert_csv_to_json(
        request: Request,
        lang: str = Form(DEFAULT_LANG),
        csv_file: UploadFile = File(...),
    ):
        current_lang = normalize_lang(lang)
        result = await service.convert_csv_to_json(
            lang=current_lang,
            csv_file=csv_file,
        )
        return render_index(
            templates=templates,
            request=request,
            result=result,
            lang=current_lang,
        )

    @app.post("/merge-json", response_class=HTMLResponse)
    async def merge_json_files(
        request: Request,
        lang: str = Form(DEFAULT_LANG),
        json_files: list[UploadFile] = File(...),
    ):
        current_lang = normalize_lang(lang)
        result = await service.merge_json_files(
            lang=current_lang,
            json_files=json_files,
        )
        return render_index(
            templates=templates,
            request=request,
            result=result,
            lang=current_lang,
        )

    @app.get("/download/{filename}")
    async def download(filename: str, lang: Optional[str] = None):
        path = storage.output_path(filename)
        if not path.exists():
            return {"error": translate(normalize_lang(lang), "file_not_found")}

        return FileResponse(
            path=path,
            media_type=storage.guess_media_type(path.name),
            filename=filename,
        )

    return app
