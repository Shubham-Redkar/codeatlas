from pathlib import Path

import pytest

from app.ingestion.languages import DetectedLanguage, detect_language


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("main.py", DetectedLanguage.PYTHON),
        ("types.pyi", DetectedLanguage.PYTHON),
        ("app.js", DetectedLanguage.JAVASCRIPT),
        ("component.jsx", DetectedLanguage.JAVASCRIPT),
        ("module.mjs", DetectedLanguage.JAVASCRIPT),
        ("config.cjs", DetectedLanguage.JAVASCRIPT),
        ("app.ts", DetectedLanguage.TYPESCRIPT),
        ("component.tsx", DetectedLanguage.TYPESCRIPT),
    ],
)
def test_detect_language(
    filename: str,
    expected: DetectedLanguage,
) -> None:
    assert detect_language(Path(filename)) == expected


def test_detect_language_returns_none_for_unknown_extension() -> None:
    assert detect_language(Path("README.md")) is None
