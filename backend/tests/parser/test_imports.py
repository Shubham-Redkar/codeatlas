from app.parser import (
    SupportedLanguage,
    extract_ast,
    extract_imports,
    parse_source,
)


def test_extract_python_imports() -> None:
    source = b"""
import os
import app.services.indexing
from pathlib import Path
from app.parser import parse_source
"""

    tree = parse_source(source, SupportedLanguage.PYTHON)
    ast = extract_ast(tree)

    imports = extract_imports(ast, SupportedLanguage.PYTHON)

    assert [item.name for item in imports] == [
        "import os",
        "import app.services.indexing",
        "from pathlib import Path",
        "from app.parser import parse_source",
    ]


def test_extract_javascript_imports() -> None:
    source = b"""
import fs from "fs";
import { parse } from "./parser";

function hello() {
    return "hello";
}
"""

    tree = parse_source(source, SupportedLanguage.JAVASCRIPT)
    ast = extract_ast(tree)

    imports = extract_imports(ast, SupportedLanguage.JAVASCRIPT)

    assert [item.name for item in imports] == [
        'import fs from "fs";',
        'import { parse } from "./parser";',
    ]
