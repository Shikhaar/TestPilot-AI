"""
TestPilot AI — Dependency Graph Builder.

Builds a directed dependency graph from AST parse results using NetworkX.
The graph captures:
  - File-level import relationships
  - Module-level call relationships (where resolvable)
  - Test-to-source coverage mappings

Graph structure:
  Nodes: file paths (relative to repo root)
  Edges: directed, labeled with edge_type and metadata

Used by the Impact Analyzer to perform BFS/DFS traversal to find
which modules are affected by a given set of changed files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx

from app.core.logging import get_logger
from app.services.ast_parser import ImportInfo, ParseResult

logger = get_logger(__name__)


class DependencyGraphBuilder:
    """Builds and queries the code dependency graph for a repository.

    The graph is built from AST parse results by resolving import paths
    to file paths. It supports:

    - BFS/DFS traversal to find all dependents of a changed file
    - Finding all files that depend on a given file (reverse lookup)
    - Serialization to/from database records

    Attributes:
        graph: The underlying NetworkX DiGraph.
        repo_root: Absolute path to the repository root.
    """

    def __init__(self, repo_root: Path) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()
        self.repo_root = repo_root

    def build(self, parse_results: list[ParseResult]) -> nx.DiGraph:
        """Build the dependency graph from a list of parse results.

        For each file, adds import edges to the files it imports.
        Import paths are resolved relative to the repository root.

        Args:
            parse_results: List of AST parse results for all repository files.

        Returns:
            The constructed NetworkX DiGraph.
        """
        # Add all files as nodes first
        for result in parse_results:
            relative_path = self._to_relative_path(result.file_path)
            self.graph.add_node(
                relative_path,
                language=result.language,
                functions=[f.name for f in result.functions],
                classes=[c.name for c in result.classes],
                is_test=self._is_test_file(relative_path),
            )

        # Build a lookup map: module name → file path
        module_map = self._build_module_map(parse_results)

        # Add import edges
        for result in parse_results:
            source_path = self._to_relative_path(result.file_path)
            for imp in result.imports:
                target_path = self._resolve_import(imp, source_path, module_map)
                if target_path and self.graph.has_node(target_path):
                    self.graph.add_edge(
                        source_path,
                        target_path,
                        edge_type="imports",
                        names=imp.names,
                        is_relative=imp.is_relative,
                    )

        logger.info(
            "Dependency graph built",
            nodes=self.graph.number_of_nodes(),
            edges=self.graph.number_of_edges(),
        )
        return self.graph

    def get_dependents(self, file_path: str, depth: int = 5) -> set[str]:
        """Find all files that depend on the given file (reverse dependencies).

        Performs BFS traversal of the REVERSED graph to find all nodes
        that (transitively) depend on file_path.

        Args:
            file_path: Relative file path.
            depth: Maximum traversal depth.

        Returns:
            Set of file paths that depend on file_path.
        """
        if not self.graph.has_node(file_path):
            return set()

        reversed_graph = self.graph.reverse()
        dependents = set()

        try:
            # BFS up to depth levels
            for node in nx.bfs_tree(reversed_graph, file_path, depth_limit=depth).nodes():
                if node != file_path:
                    dependents.add(node)
        except nx.NetworkXError:
            pass

        return dependents

    def get_dependencies(self, file_path: str, depth: int = 3) -> set[str]:
        """Find all files that the given file depends on.

        Args:
            file_path: Relative file path.
            depth: Maximum traversal depth.

        Returns:
            Set of file paths that file_path depends on.
        """
        if not self.graph.has_node(file_path):
            return set()

        dependencies = set()
        try:
            for node in nx.bfs_tree(self.graph, file_path, depth_limit=depth).nodes():
                if node != file_path:
                    dependencies.add(node)
        except nx.NetworkXError:
            pass

        return dependencies

    def get_affected_by_changes(
        self,
        changed_files: list[str],
        depth: int = 5,
    ) -> dict[str, set[str]]:
        """Find all modules affected by a set of changed files.

        For each changed file, performs reverse BFS traversal to find
        all modules that transitively depend on it.

        Args:
            changed_files: List of relative file paths that changed.
            depth: Maximum graph traversal depth.

        Returns:
            Dictionary mapping each changed file to its set of dependents.
        """
        affected: dict[str, set[str]] = {}
        for file_path in changed_files:
            dependents = self.get_dependents(file_path, depth=depth)
            affected[file_path] = dependents
            logger.debug(
                "Found dependents for changed file",
                file=file_path,
                dependents=len(dependents),
            )
        return affected

    def get_test_files_for(self, file_path: str) -> list[str]:
        """Find test files that test the given source file.

        Checks both:
        1. Direct test edges in the graph (explicit test coverage)
        2. Naming convention heuristics (test_foo.py → foo.py)

        Args:
            file_path: Relative path to a source file.

        Returns:
            List of test file paths.
        """
        test_files = []

        # Check all test nodes in the graph
        for node, data in self.graph.nodes(data=True):
            if not data.get("is_test"):
                continue
            # Check if test file imports the source file
            if self.graph.has_edge(node, file_path) or self._matches_test_convention(
                node, file_path
            ):
                test_files.append(node)

        return test_files

    def find_critical_nodes(self, top_n: int = 20) -> list[tuple[str, float]]:
        """Find the most critical nodes by in-degree centrality.

        Nodes with high in-degree are depended on by many other modules
        and represent high-risk change targets.

        Args:
            top_n: Number of top critical nodes to return.

        Returns:
            List of (node_path, centrality_score) tuples sorted by score.
        """
        if self.graph.number_of_nodes() == 0:
            return []

        centrality = nx.in_degree_centrality(self.graph)
        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:top_n]

    def to_edge_records(self, repository_id: str) -> list[dict[str, Any]]:
        """Serialize the graph edges to database records.

        Args:
            repository_id: The repository UUID.

        Returns:
            List of dictionaries suitable for bulk insert into dependency_graph table.
        """
        records = []
        for source, target, data in self.graph.edges(data=True):
            records.append(
                {
                    "repository_id": repository_id,
                    "source_node": source,
                    "target_node": target,
                    "source_type": "file",
                    "target_type": "file",
                    "edge_type": data.get("edge_type", "imports"),
                    "metadata_json": json.dumps({"names": data.get("names", [])}),
                }
            )
        return records

    @classmethod
    def from_edge_records(
        cls,
        records: list[dict[str, Any]],
        repo_root: Path,
    ) -> DependencyGraphBuilder:
        """Reconstruct the graph from database edge records.

        Args:
            records: List of dependency_graph table records.
            repo_root: Repository root path.

        Returns:
            A DependencyGraphBuilder instance with the graph populated.
        """
        builder = cls(repo_root)
        for record in records:
            builder.graph.add_edge(
                record["source_node"],
                record["target_node"],
                edge_type=record.get("edge_type", "imports"),
            )
        return builder

    # --------------------------------------------------------------------------
    # Private helpers
    # --------------------------------------------------------------------------

    def _to_relative_path(self, absolute_path: str) -> str:
        """Convert an absolute path to a path relative to repo_root."""
        try:
            return str(Path(absolute_path).relative_to(self.repo_root))
        except ValueError:
            return absolute_path

    def _build_module_map(self, parse_results: list[ParseResult]) -> dict[str, str]:
        """Build a mapping from module name to relative file path."""
        module_map: dict[str, str] = {}
        for result in parse_results:
            rel_path = self._to_relative_path(result.file_path)
            # Python module name: remove extension, replace / with .
            lang = result.language
            path = Path(rel_path)
            if lang == "python":
                module_name = str(path.with_suffix("")).replace("/", ".").replace("\\", ".")
                module_map[module_name] = rel_path
                # Also map the basename
                module_map[path.stem] = rel_path
        return module_map

    def _resolve_import(
        self,
        imp: ImportInfo,
        source_path: str,
        module_map: dict[str, str],
    ) -> str | None:
        """Resolve an import statement to a file path.

        Args:
            imp: The import info extracted by AST parser.
            source_path: Relative path of the file containing this import.
            module_map: Mapping of module names to file paths.

        Returns:
            Resolved relative file path or None if unresolvable.
        """
        module = imp.module

        # Try direct module map lookup
        if module in module_map:
            return module_map[module]

        # Try partial match (last segment)
        last_segment = module.split(".")[-1]
        if last_segment in module_map:
            return module_map[last_segment]

        # Relative imports: resolve relative to source file directory
        if imp.is_relative:
            source_dir = Path(source_path).parent
            candidate = source_dir / module.replace(".", "/")
            for ext in (".py", ".js", ".ts"):
                candidate_with_ext = str(candidate) + ext
                if candidate_with_ext in module_map.values():
                    return candidate_with_ext

        return None

    @staticmethod
    def _is_test_file(file_path: str) -> bool:
        """Check if a file path follows test naming conventions."""
        name = Path(file_path).name.lower()
        return (
            name.startswith("test_")
            or name.endswith("_test.py")
            or name.endswith(".test.js")
            or name.endswith(".test.ts")
            or name.endswith(".spec.js")
            or name.endswith(".spec.ts")
            or "/tests/" in file_path
            or "/test/" in file_path
            or "/__tests__/" in file_path
        )

    @staticmethod
    def _matches_test_convention(test_path: str, source_path: str) -> bool:
        """Check if a test file covers a source file by naming convention."""
        source_name = Path(source_path).stem
        test_name = Path(test_path).stem
        return (
            test_name == f"test_{source_name}"
            or test_name == f"{source_name}_test"
            or test_name == f"{source_name}.test"
            or test_name == f"{source_name}.spec"
        )
