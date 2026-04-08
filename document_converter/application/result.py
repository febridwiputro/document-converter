from dataclasses import dataclass
from typing import Optional


@dataclass
class UseCaseResult:
    mode: str
    status_code: int = 200
    download: Optional[str] = None
    error: Optional[str] = None
    message: Optional[str] = None
