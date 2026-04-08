# document-converter
document-converter

## Layered Architecture

Struktur backend sekarang dipisah agar lebih dekat ke clean architecture:

- `document_converter/presentation`
  - FastAPI routes, HTTP request/response, render template.
- `document_converter/application`
  - Orkestrasi use-case (`ConverterService`) dan output contract (`UseCaseResult`).
- `document_converter/domain`
  - Logika inti murni (proses PDF/image dan validasi JSON key).
- `document_converter/infrastructure`
  - Akses file system (upload/output storage, MIME type).
- `document_converter/core`
  - Konfigurasi path, constants, dan mode converter.

`app.py` sekarang hanya composition root untuk membuat instance FastAPI dari layer presentation.
