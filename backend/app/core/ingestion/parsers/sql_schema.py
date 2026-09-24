"""Parser for SQL DDL schema files."""

import re
from pathlib import Path

from app.core.ingestion.types import IngestionResult, ParsedEdge, ParsedNode


def parse_sql_schema(content: str, file_path: str = "schema.sql") -> IngestionResult:
    """Parse SQL schema and extract tables, columns, foreign keys, and database entities."""
    result = IngestionResult()
    db_name = Path(file_path).stem.replace(".", "_") or "primary_db"

    db_node = ParsedNode(
        name=db_name,
        node_type="database",
        path=file_path,
        properties={"dialect": "sql", "source_file": file_path},
    )
    result.nodes.append(db_node)

    # Match CREATE TABLE statements: CREATE TABLE [IF NOT EXISTS] `?([a-zA-Z0-9_]+)`?\s*\((.*?)\);
    table_pattern = re.compile(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:`|\")?([a-zA-Z0-9_]+)(?:`|\")?\s*\((.*?)\);",
        re.DOTALL | re.IGNORECASE,
    )

    for match in table_pattern.finditer(content):
        table_name = match.group(1).lower()
        body = match.group(2)

        # Extract column names (lines that don't start with constraint, primary key, foreign key, key)
        columns = []
        foreign_keys = []

        for line in body.split(","):
            cleaned = line.strip()
            if not cleaned:
                continue

            # Foreign key: FOREIGN KEY (col) REFERENCES other_table(col)
            fk_match = re.search(
                r"FOREIGN\s+KEY\s*\([^)]+\)\s*REFERENCES\s+(?:`|\")?([a-zA-Z0-9_]+)(?:`|\")?",
                cleaned,
                re.IGNORECASE,
            )
            if fk_match:
                foreign_keys.append(fk_match.group(1).lower())
                continue

            if re.match(r"^(PRIMARY\s+KEY|KEY|INDEX|CONSTRAINT|UNIQUE)", cleaned, re.IGNORECASE):
                continue

            col_parts = cleaned.split()
            if col_parts:
                col_name = col_parts[0].replace("`", "").replace('"', "")
                col_type = col_parts[1] if len(col_parts) > 1 else "unknown"
                columns.append({"name": col_name, "type": col_type})

        table_node = ParsedNode(
            name=table_name,
            node_type="table",
            path=file_path,
            properties={"columns": columns, "database": db_name},
        )
        result.nodes.append(table_node)

        # Edge: database contains table
        result.edges.append(
            ParsedEdge(
                source_name=db_name,
                source_type="database",
                target_name=table_name,
                target_type="table",
                relationship_type="contains",
            )
        )

        # Foreign key dependencies: table reads_from or depends_on referenced table
        for ref_table in foreign_keys:
            result.edges.append(
                ParsedEdge(
                    source_name=table_name,
                    source_type="table",
                    target_name=ref_table,
                    target_type="table",
                    relationship_type="depends_on",
                    properties={"kind": "foreign_key"},
                )
            )

    return result
