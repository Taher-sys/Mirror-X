"""Parser for Markdown documentation files."""

import re
from pathlib import Path

from app.core.ingestion.types import IngestionResult, ParsedEdge, ParsedNode


def parse_markdown(content: str, file_path: str = "README.md") -> IngestionResult:
    """Parse Markdown documentation and extract documentation nodes and entity linkages."""
    result = IngestionResult()

    # Extract title from first # heading or filename
    title_match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
    doc_title = title_match.group(1).strip() if title_match else Path(file_path).stem

    # Extract section headings
    sections = re.findall(r"^##+\s+(.+)", content, re.MULTILINE)

    # Extract referenced URLs and API endpoints (e.g., /api/v1/..., /users, etc.)
    endpoint_refs = list(set(re.findall(r"(/api/v\d+/[a-zA-Z0-9_\-/]+)", content)))

    # Extract backtick symbols (potential service, model, or table references)
    symbol_refs = list(set(re.findall(r"`([a-zA-Z0-9_]{3,30})`", content)))

    doc_node = ParsedNode(
        name=doc_title,
        node_type="documentation",
        path=file_path,
        properties={
            "sections": sections,
            "referenced_endpoints": endpoint_refs,
            "referenced_symbols": symbol_refs[:20],
            "word_count": len(content.split()),
        },
    )
    result.nodes.append(doc_node)

    # If the doc mentions known endpoints, create `documents` edges
    for ep in endpoint_refs:
        result.edges.append(
            ParsedEdge(
                source_name=doc_title,
                source_type="documentation",
                target_name=ep,
                target_type="api",
                relationship_type="documents",
            )
        )

    return result
