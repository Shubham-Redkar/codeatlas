import pytest

from app.core.exceptions import UnsupportedLanguageError
from app.parser import (
    SupportedLanguage,
    extract_ast,
    extract_imports,
    parse_source,
)


def test_extract_imports_rejects_unsupported_language() -> None:
    tree = parse_source(
        b"import os\n",
        SupportedLanguage.PYTHON,
    )
    ast = extract_ast(tree)

    with pytest.raises(UnsupportedLanguageError, match="Unsupported language"):
        extract_imports(ast, "ruby")


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


def test_extract_python_import_metadata() -> None:
    source = b"from pathlib import Path as FilePath\nimport os.path as path\n"

    tree = parse_source(source, SupportedLanguage.PYTHON)
    ast = extract_ast(tree)

    imports = extract_imports(ast, SupportedLanguage.PYTHON)

    assert imports[0].module == "pathlib"
    assert imports[0].imported_names == ("Path",)
    assert imports[0].aliases == (("Path", "FilePath"),)

    assert imports[1].module == ""
    assert imports[1].imported_names == ("os.path",)
    assert imports[1].aliases == (("os.path", "path"),)


def test_extract_javascript_import_metadata() -> None:
    source = b'import { parse as parseCode } from "./parser";\n'

    tree = parse_source(source, SupportedLanguage.JAVASCRIPT)
    ast = extract_ast(tree)

    imports = extract_imports(ast, SupportedLanguage.JAVASCRIPT)

    assert imports[0].module == "./parser"
    assert imports[0].imported_names == ("parse",)
    assert imports[0].aliases == (("parse", "parseCode"),)


def test_extract_python_imports_with_malformed_syntax() -> None:
    source = b"""
from pathlib import (
import os
"""

    tree = parse_source(source, SupportedLanguage.PYTHON)
    ast = extract_ast(tree)

    imports = extract_imports(ast, SupportedLanguage.PYTHON)

    assert tree.root_node.has_error is True
    assert isinstance(imports, list)


def test_extract_typescript_import_metadata() -> None:
    source = b"""
import React from "react";
import { useState as useLocalState, useEffect } from "react";
import * as utils from "./utils";
import type { User } from "./types";
"""

    tree = parse_source(source, SupportedLanguage.TYPESCRIPT)
    ast = extract_ast(tree)

    imports = extract_imports(ast, SupportedLanguage.TYPESCRIPT)

    assert [item.module for item in imports] == [
        "react",
        "react",
        "./utils",
        "./types",
    ]
    assert imports[0].imported_names == ("default",)
    assert imports[0].aliases == (("default", "React"),)
    assert imports[1].imported_names == ("useState", "useEffect")
    assert imports[1].aliases == (
        ("useState", "useLocalState"),
        ("useEffect", "useEffect"),
    )
    assert imports[2].imported_names == ("*",)
    assert imports[2].aliases == (("*", "utils"),)
    assert imports[3].imported_names == ("User",)
    assert imports[3].aliases == (("User", "User"),)
