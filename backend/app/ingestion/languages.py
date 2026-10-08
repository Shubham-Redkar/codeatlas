from enum import StrEnum
from pathlib import Path


class DetectedLanguage(StrEnum):
    """Supported programming languages detected by CodeAtlas."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"


_LANGUAGE_BY_SUFFIX = {
    ".py": DetectedLanguage.PYTHON,
    ".pyi": DetectedLanguage.PYTHON,
    ".js": DetectedLanguage.JAVASCRIPT,
    ".jsx": DetectedLanguage.JAVASCRIPT,
    ".mjs": DetectedLanguage.JAVASCRIPT,
    ".cjs": DetectedLanguage.JAVASCRIPT,
    ".ts": DetectedLanguage.TYPESCRIPT,
    ".tsx": DetectedLanguage.TYPESCRIPT,
}


def detect_language(
    path: Path,
) -> DetectedLanguage | None:
    """
    Detect the programming language from a file's extension.
    """
    return _LANGUAGE_BY_SUFFIX.get(path.suffix.lower())
