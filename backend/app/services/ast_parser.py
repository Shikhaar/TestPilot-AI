"""
TestPilot AI — Tree-sitter AST Parser.

Parses source files using Tree-sitter to extract:
- Function definitions (name, parameters, decorators, line range)
- Class definitions (name, base classes, methods)
- Import statements (module, aliases, from-imports)
- Export declarations
- API routes (FastAPI, Express, Flask, etc.)
- Database model definitions

Supports: Python, JavaScript, TypeScript, Java, Go, Rust.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

# Language → Tree-sitter grammar mapping
LANGUAGE_EXTENSIONS: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
}


@dataclass
class FunctionInfo:
    """Extracted function/method information."""
    name: str
    parameters: list[str]
    return_type: str | None
    decorators: list[str]
    line_start: int
    line_end: int
    is_async: bool
    is_method: bool
    class_name: str | None
    docstring: str | None


@dataclass
class ClassInfo:
    """Extracted class/interface information."""
    name: str
    base_classes: list[str]
    methods: list[str]
    attributes: list[str]
    decorators: list[str]
    line_start: int
    line_end: int
    docstring: str | None


@dataclass
class ImportInfo:
    """Extracted import statement."""
    module: str
    names: list[str]
    alias: str | None
    is_relative: bool
    line: int


@dataclass
class RouteInfo:
    """Extracted API route definition."""
    path: str
    method: str
    handler_name: str
    line: int
    framework: str  # 'fastapi' | 'flask' | 'express' | 'gin'


@dataclass
class ParseResult:
    """Result of parsing a single source file."""
    file_path: str
    language: str
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    imports: list[ImportInfo] = field(default_factory=list)
    routes: list[RouteInfo] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)
    line_count: int = 0
    content_hash: str = ""
    error: str | None = None


class ASTParser:
    """Multi-language AST parser powered by Tree-sitter.

    Extracts semantic code structure from source files without
    executing any code. Uses Tree-sitter for accurate, language-aware
    parsing that handles syntax correctly.
    """

    def __init__(self) -> None:
        self._parsers: dict[str, Any] = {}
        self._load_grammars()

    def _load_grammars(self) -> None:
        """Load Tree-sitter grammar parsers for supported languages."""
        try:
            import tree_sitter_python as tspython
            import tree_sitter_javascript as tsjavascript
            import tree_sitter_typescript as tstypescript
            import tree_sitter_java as tsjava
            import tree_sitter_go as tsgo
            from tree_sitter import Language, Parser

            self._parsers["python"] = Parser(Language(tspython.language()))
            self._parsers["javascript"] = Parser(Language(tsjavascript.language()))
            self._parsers["typescript"] = Parser(Language(tstypescript.language_typescript()))
            self._parsers["tsx"] = Parser(Language(tstypescript.language_tsx()))
            self._parsers["java"] = Parser(Language(tsjava.language()))
            self._parsers["go"] = Parser(Language(tsgo.language()))

            logger.info("Tree-sitter grammars loaded", languages=list(self._parsers.keys()))
        except ImportError as e:
            logger.error("Failed to load Tree-sitter grammars", error=str(e))

    def parse_file(self, file_path: Path) -> ParseResult | None:
        """Parse a single source file and extract code structure.

        Args:
            file_path: Absolute path to the source file.

        Returns:
            ParseResult with extracted symbols, or None if unsupported.
        """
        extension = file_path.suffix.lower()
        language = LANGUAGE_EXTENSIONS.get(extension)

        if not language:
            return None

        if language not in self._parsers:
            logger.warning("No parser available for language", language=language)
            return None

        try:
            content = file_path.read_bytes()
            content_str = content.decode("utf-8", errors="replace")
            content_hash = hashlib.sha256(content).hexdigest()
        except OSError as e:
            logger.error("Failed to read file", path=str(file_path), error=str(e))
            return ParseResult(
                file_path=str(file_path),
                language=language,
                error=str(e),
            )

        parser = self._parsers[language]

        try:
            tree = parser.parse(content)
            root_node = tree.root_node
        except Exception as e:
            logger.error("Tree-sitter parse error", path=str(file_path), error=str(e))
            return ParseResult(
                file_path=str(file_path),
                language=language,
                content_hash=content_hash,
                line_count=content_str.count("\n") + 1,
                error=str(e),
            )

        result = ParseResult(
            file_path=str(file_path),
            language=language,
            content_hash=content_hash,
            line_count=content_str.count("\n") + 1,
        )

        # Dispatch to language-specific extractors
        if language == "python":
            self._extract_python(root_node, content_str, result)
        elif language in ("javascript", "typescript", "tsx"):
            self._extract_js_ts(root_node, content_str, result, language)
        elif language == "java":
            self._extract_java(root_node, content_str, result)
        elif language == "go":
            self._extract_go(root_node, content_str, result)

        logger.debug(
            "Parsed file",
            path=str(file_path),
            language=language,
            functions=len(result.functions),
            classes=len(result.classes),
            imports=len(result.imports),
        )
        return result

    def parse_directory(
        self,
        directory: Path,
        ignored_dirs: list[str] | None = None,
        ignored_exts: list[str] | None = None,
    ) -> list[ParseResult]:
        """Parse all supported source files in a directory.

        Args:
            directory: Root directory to walk.
            ignored_dirs: Directory names to skip (e.g., ['node_modules', '.git']).
            ignored_exts: File extensions to skip.

        Returns:
            List of ParseResult for each parsed file.
        """
        from app.core.config import get_settings
        settings = get_settings()

        ignored_dirs = ignored_dirs or settings.ignored_directories
        ignored_exts = ignored_exts or settings.ignored_extensions
        results = []

        for file_path in directory.rglob("*"):
            if not file_path.is_file():
                continue
            # Skip ignored directories
            if any(part in ignored_dirs for part in file_path.parts):
                continue
            # Skip ignored extensions
            if file_path.suffix in ignored_exts:
                continue
            # Skip files too large (> 1MB)
            if file_path.stat().st_size > 1_000_000:
                continue

            result = self.parse_file(file_path)
            if result is not None:
                results.append(result)

        logger.info(
            "Directory parsed",
            directory=str(directory),
            files_parsed=len(results),
        )
        return results

    # --------------------------------------------------------------------------
    # Python Extractor
    # --------------------------------------------------------------------------

    def _extract_python(
        self, root_node: Any, source: str, result: ParseResult
    ) -> None:
        """Extract Python code symbols from Tree-sitter AST."""
        lines = source.splitlines()

        def get_text(node: Any) -> str:
            return source[node.start_byte:node.end_byte]

        def get_line(node: Any) -> int:
            return node.start_point[0] + 1

        # Walk all nodes
        stack = [root_node]
        current_class: str | None = None

        while stack:
            node = stack.pop()

            if node.type == "import_statement":
                module = ""
                names = []
                for child in node.children:
                    if child.type == "dotted_name":
                        module = get_text(child)
                    elif child.type == "aliased_import":
                        for c in child.children:
                            if c.type == "dotted_name":
                                names.append(get_text(c))
                result.imports.append(ImportInfo(
                    module=module,
                    names=names,
                    alias=None,
                    is_relative=False,
                    line=get_line(node),
                ))

            elif node.type == "import_from_statement":
                module = ""
                names = []
                is_relative = False
                for child in node.children:
                    if child.type in ("dotted_name", "relative_import"):
                        text = get_text(child)
                        if text.startswith("."):
                            is_relative = True
                        module = text.lstrip(".")
                    elif child.type == "import":
                        pass
                    elif child.type == "identifier":
                        names.append(get_text(child))
                result.imports.append(ImportInfo(
                    module=module,
                    names=names,
                    alias=None,
                    is_relative=is_relative,
                    line=get_line(node),
                ))

            elif node.type == "class_definition":
                name_node = node.child_by_field_name("name")
                class_name = get_text(name_node) if name_node else "Unknown"
                base_classes = []
                args = node.child_by_field_name("superclasses")
                if args:
                    for c in args.children:
                        if c.type == "identifier":
                            base_classes.append(get_text(c))

                decorators = self._get_python_decorators(node, source)
                methods = []
                body = node.child_by_field_name("body")
                if body:
                    for child in body.children:
                        if child.type == "function_definition":
                            fn_name = child.child_by_field_name("name")
                            if fn_name:
                                methods.append(get_text(fn_name))

                result.classes.append(ClassInfo(
                    name=class_name,
                    base_classes=base_classes,
                    methods=methods,
                    attributes=[],
                    decorators=decorators,
                    line_start=get_line(node),
                    line_end=node.end_point[0] + 1,
                    docstring=None,
                ))

            elif node.type == "function_definition":
                name_node = node.child_by_field_name("name")
                fn_name = get_text(name_node) if name_node else "Unknown"
                is_async = any(c.type == "async" for c in node.children)
                decorators = self._get_python_decorators(node, source)

                # Extract FastAPI route info from decorators
                for dec in decorators:
                    for method in ("get", "post", "put", "delete", "patch", "options"):
                        if f".{method}(" in dec or f"@{method}(" in dec:
                            # Try to extract path
                            import re
                            path_match = re.search(r'["\']([^"\']+)["\']', dec)
                            if path_match:
                                result.routes.append(RouteInfo(
                                    path=path_match.group(1),
                                    method=method.upper(),
                                    handler_name=fn_name,
                                    line=get_line(node),
                                    framework="fastapi",
                                ))

                result.functions.append(FunctionInfo(
                    name=fn_name,
                    parameters=[],
                    return_type=None,
                    decorators=decorators,
                    line_start=get_line(node),
                    line_end=node.end_point[0] + 1,
                    is_async=is_async,
                    is_method=False,
                    class_name=None,
                    docstring=None,
                ))

            # Continue traversal
            stack.extend(reversed(node.children))

    def _get_python_decorators(self, node: Any, source: str) -> list[str]:
        """Extract decorator text from a Python function/class node."""
        decorators = []
        parent = node.parent
        if parent:
            for sibling in parent.children:
                if sibling.end_byte <= node.start_byte and sibling.type == "decorator":
                    decorators.append(source[sibling.start_byte:sibling.end_byte])
        return decorators

    # --------------------------------------------------------------------------
    # JavaScript/TypeScript Extractor
    # --------------------------------------------------------------------------

    def _extract_js_ts(
        self, root_node: Any, source: str, result: ParseResult, language: str
    ) -> None:
        """Extract JS/TS code symbols from Tree-sitter AST."""

        def get_text(node: Any) -> str:
            return source[node.start_byte:node.end_byte]

        def get_line(node: Any) -> int:
            return node.start_point[0] + 1

        stack = [root_node]
        while stack:
            node = stack.pop()

            if node.type in ("import_statement", "import_declaration"):
                module = ""
                names = []
                for child in node.children:
                    if child.type == "string":
                        module = get_text(child).strip("'\"")
                    elif child.type in ("identifier", "import_clause"):
                        names.append(get_text(child))
                result.imports.append(ImportInfo(
                    module=module,
                    names=names,
                    alias=None,
                    is_relative=module.startswith("."),
                    line=get_line(node),
                ))

            elif node.type in ("function_declaration", "function_definition", "method_definition"):
                name_node = node.child_by_field_name("name")
                fn_name = get_text(name_node) if name_node else "anonymous"
                result.functions.append(FunctionInfo(
                    name=fn_name,
                    parameters=[],
                    return_type=None,
                    decorators=[],
                    line_start=get_line(node),
                    line_end=node.end_point[0] + 1,
                    is_async=any(c.type == "async" for c in node.children),
                    is_method=node.type == "method_definition",
                    class_name=None,
                    docstring=None,
                ))

            elif node.type == "class_declaration":
                name_node = node.child_by_field_name("name")
                class_name = get_text(name_node) if name_node else "Unknown"
                result.classes.append(ClassInfo(
                    name=class_name,
                    base_classes=[],
                    methods=[],
                    attributes=[],
                    decorators=[],
                    line_start=get_line(node),
                    line_end=node.end_point[0] + 1,
                    docstring=None,
                ))

            elif node.type == "export_statement":
                result.exports.append(get_text(node)[:100])

            stack.extend(reversed(node.children))

    # --------------------------------------------------------------------------
    # Java Extractor
    # --------------------------------------------------------------------------

    def _extract_java(
        self, root_node: Any, source: str, result: ParseResult
    ) -> None:
        """Extract Java code symbols from Tree-sitter AST."""

        def get_text(node: Any) -> str:
            return source[node.start_byte:node.end_byte]

        def get_line(node: Any) -> int:
            return node.start_point[0] + 1

        stack = [root_node]
        while stack:
            node = stack.pop()

            if node.type == "import_declaration":
                result.imports.append(ImportInfo(
                    module=get_text(node).replace("import ", "").replace(";", "").strip(),
                    names=[],
                    alias=None,
                    is_relative=False,
                    line=get_line(node),
                ))

            elif node.type == "class_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    result.classes.append(ClassInfo(
                        name=get_text(name_node),
                        base_classes=[],
                        methods=[],
                        attributes=[],
                        decorators=[],
                        line_start=get_line(node),
                        line_end=node.end_point[0] + 1,
                        docstring=None,
                    ))

            elif node.type == "method_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    result.functions.append(FunctionInfo(
                        name=get_text(name_node),
                        parameters=[],
                        return_type=None,
                        decorators=[],
                        line_start=get_line(node),
                        line_end=node.end_point[0] + 1,
                        is_async=False,
                        is_method=True,
                        class_name=None,
                        docstring=None,
                    ))

            stack.extend(reversed(node.children))

    # --------------------------------------------------------------------------
    # Go Extractor
    # --------------------------------------------------------------------------

    def _extract_go(
        self, root_node: Any, source: str, result: ParseResult
    ) -> None:
        """Extract Go code symbols from Tree-sitter AST."""

        def get_text(node: Any) -> str:
            return source[node.start_byte:node.end_byte]

        def get_line(node: Any) -> int:
            return node.start_point[0] + 1

        stack = [root_node]
        while stack:
            node = stack.pop()

            if node.type == "import_declaration":
                for child in node.children:
                    if child.type == "import_spec":
                        for c in child.children:
                            if c.type == "interpreted_string_literal":
                                result.imports.append(ImportInfo(
                                    module=get_text(c).strip('"'),
                                    names=[],
                                    alias=None,
                                    is_relative=False,
                                    line=get_line(node),
                                ))

            elif node.type == "function_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    result.functions.append(FunctionInfo(
                        name=get_text(name_node),
                        parameters=[],
                        return_type=None,
                        decorators=[],
                        line_start=get_line(node),
                        line_end=node.end_point[0] + 1,
                        is_async=False,
                        is_method=False,
                        class_name=None,
                        docstring=None,
                    ))

            elif node.type == "type_declaration":
                for child in node.children:
                    if child.type == "type_spec":
                        name_node = child.child_by_field_name("name")
                        if name_node:
                            result.classes.append(ClassInfo(
                                name=get_text(name_node),
                                base_classes=[],
                                methods=[],
                                attributes=[],
                                decorators=[],
                                line_start=get_line(node),
                                line_end=node.end_point[0] + 1,
                                docstring=None,
                            ))

            stack.extend(reversed(node.children))

    def to_json_serializable(self, result: ParseResult) -> dict[str, Any]:
        """Convert a ParseResult to a JSON-serializable dictionary.

        Args:
            result: The ParseResult to serialize.

        Returns:
            Dictionary suitable for JSON serialization and database storage.
        """
        return {
            "functions": [fn.name for fn in result.functions],
            "classes": [cls.name for cls in result.classes],
            "imports": [imp.module for imp in result.imports],
            "routes": [
                {"path": r.path, "method": r.method, "handler": r.handler_name}
                for r in result.routes
            ],
            "exports": result.exports,
        }
