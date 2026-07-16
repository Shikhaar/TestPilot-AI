"""TestPilot AI — AST Parser Tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from app.services.ast_parser import ASTParser


@pytest.fixture
def parser() -> ASTParser:
    return ASTParser()


def test_parse_python_file(parser: ASTParser) -> None:
    """Test parsing a simple Python code file to extract symbols."""
    content = """
import os
from sys import exit

@decorator
class SampleClass:
    def method_one(self):
        pass

async def async_function(param1, param2):
    \"\"\"This is a docstring.\"\"\"
    return param1
"""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
        tmp.write(content.encode())
        tmp_path = Path(tmp.name)

    try:
        result = parser.parse_file(tmp_path)
        assert result is not None
        assert result.language == "python"

        # Check imports
        imports = [imp.module for imp in result.imports]
        assert "os" in imports
        assert "sys" in imports

        # Check classes
        classes = [cls.name for cls in result.classes]
        assert "SampleClass" in classes

        # Check functions
        functions = [fn.name for fn in result.functions]
        # method_one is a function inside class, parser grabs all functions/methods
        assert "method_one" in functions
        assert "async_function" in functions

    finally:
        tmp_path.unlink()
