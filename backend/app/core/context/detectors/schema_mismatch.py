"""Schema mismatch detector."""

from typing import Any

from app.core.context.detectors.base import BaseDetector, DiscrepancyResult


class SchemaMismatchDetector(BaseDetector):
    """Detects type, nullability, and structural drift between database schemas and models/APIs."""

    detector_type = "schema_mismatch"

    def detect(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        file_tree: dict[str, str] | None = None,
    ) -> list[DiscrepancyResult]:
        results: list[DiscrepancyResult] = []

        table_nodes = [n for n in nodes if n.get("node_type") == "table"]
        model_nodes = [n for n in nodes if n.get("node_type") == "model"]

        tables_by_name = {t.get("name", "").lower(): t for t in table_nodes}

        for m in model_nodes:
            m_props = m.get("properties", {}) or {}
            m_name = m.get("name", "")
            table_name = m_props.get("table_name", m_name).lower()

            t_node = tables_by_name.get(table_name)
            if not t_node:
                continue

            t_props = t_node.get("properties", {}) or {}
            table_cols = {c.get("name", "").lower(): c for c in t_props.get("columns", [])}
            model_fields = m_props.get("fields", [])

            for f in model_fields:
                if not isinstance(f, dict):
                    continue
                fname = f.get("name", "").lower()
                ftype = f.get("type", "").lower()
                nullable = f.get("nullable", True)

                col = table_cols.get(fname)
                if not col:
                    # Column defined in model but missing in database schema DDL
                    results.append(
                        DiscrepancyResult(
                            title=f"Missing DB Column: '{fname}' in table '{table_name}'",
                            finding_type=self.detector_type,
                            severity="high",
                            confidence=0.96,
                            description=(
                                f"Model '{m_name}' declares attribute '{fname}', but column does not exist "
                                f"in database schema DDL for table '{table_name}'."
                            ),
                            file_path=m.get("path") or t_node.get("path"),
                            expected=f"Column '{fname}' defined in {table_name}",
                            actual="Column not found in DDL",
                            related_node_ids=[nid for nid in [m.get("id"), t_node.get("id")] if nid],
                            metadata={"table": table_name, "missing_column": fname},
                        )
                    )
                    continue

                col_type = col.get("type", "").lower()
                col_nullable = col.get("nullable", True)

                # Type mismatch check
                type_conflict = False
                if ("int" in col_type or "bigint" in col_type or "smallint" in col_type) and ("str" in ftype or "string" in ftype or "text" in ftype) or ("varchar" in col_type or "text" in col_type or "string" in col_type) and ("int" in ftype or "integer" in ftype or "float" in ftype or "number" in ftype) or ("bool" in col_type) and ("str" in ftype or "int" in ftype):
                    type_conflict = True

                if type_conflict:
                    results.append(
                        DiscrepancyResult(
                            title=f"Data Type Mismatch on '{table_name}.{fname}'",
                            finding_type=self.detector_type,
                            severity="critical",
                            confidence=0.98,
                            description=(
                                f"Type conflict: Model '{m_name}' defines field '{fname}' as '{ftype}', "
                                f"whereas database schema specifies '{col.get('type')}'."
                            ),
                            file_path=m.get("path") or t_node.get("path"),
                            expected=col.get("type"),
                            actual=ftype,
                            related_node_ids=[nid for nid in [m.get("id"), t_node.get("id")] if nid],
                            metadata={"field": fname, "model_type": ftype, "sql_type": col.get("type")},
                        )
                    )

                # Nullability mismatch check: SQL requires NOT NULL, but Model allows NULL
                if not col_nullable and nullable:
                    results.append(
                        DiscrepancyResult(
                            title=f"Nullability Drift on '{table_name}.{fname}'",
                            finding_type=self.detector_type,
                            severity="high",
                            confidence=0.93,
                            description=(
                                f"Database schema enforces NOT NULL on '{table_name}.{fname}', "
                                f"but model '{m_name}' marks field as optional/nullable."
                            ),
                            file_path=m.get("path") or t_node.get("path"),
                            expected="NOT NULL (required)",
                            actual="Nullable / Optional",
                            related_node_ids=[nid for nid in [m.get("id"), t_node.get("id")] if nid],
                            metadata={"field": fname, "sql_nullable": False, "model_nullable": True},
                        )
                    )

        return results
