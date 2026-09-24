"""Naming mismatch detector."""

from typing import Any

from app.core.context.detectors.base import BaseDetector, DiscrepancyResult


class NamingMismatchDetector(BaseDetector):
    """Detects naming discrepancies between database schemas, models, and ORM entities."""

    detector_type = "naming_mismatch"

    def detect(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        file_tree: dict[str, str] | None = None,
    ) -> list[DiscrepancyResult]:
        results: list[DiscrepancyResult] = []

        table_nodes = [n for n in nodes if n.get("node_type") == "table"]
        model_nodes = [n for n in nodes if n.get("node_type") == "model"]

        # Map tables by clean name
        tables_by_name: dict[str, dict[str, Any]] = {}
        for t in table_nodes:
            tname = t.get("name", "").lower()
            tables_by_name[tname] = t

        for m in model_nodes:
            m_props = m.get("properties", {}) or {}
            m_name = m.get("name", "")
            target_table = m_props.get("table_name", m_name).lower()

            # Check if model references a table name that differs slightly or has mismatch
            # E.g. Model User references table "users" or "user_accounts"
            matched_table = tables_by_name.get(target_table)
            if not matched_table:
                # Check if there is a similar or pluralized table that is mismatched
                singular_m = target_table.rstrip("s")
                potential_match = None
                for tname in tables_by_name:
                    if tname.rstrip("s") == singular_m or tname == f"{target_table}s" or tname.replace("_", "") == target_table.replace("_", ""):
                        potential_match = tname
                        break

                if potential_match and potential_match != target_table:
                    t_node = tables_by_name[potential_match]
                    results.append(
                        DiscrepancyResult(
                            title=f"Table Naming Mismatch: Model '{m_name}' vs Table '{potential_match}'",
                            finding_type=self.detector_type,
                            severity="medium",
                            confidence=0.89,
                            description=(
                                f"Model '{m_name}' expects table '{target_table}', but database schema defines "
                                f"table as '{potential_match}'."
                            ),
                            file_path=m.get("path") or t_node.get("path"),
                            expected=potential_match,
                            actual=target_table,
                            related_node_ids=[nid for nid in [m.get("id"), t_node.get("id")] if nid],
                            metadata={"model": m_name, "table": potential_match},
                        )
                    )

            # Check column vs field naming discrepancies
            if matched_table:
                table_cols = {c.get("name", "").lower(): c for c in matched_table.get("properties", {}).get("columns", [])}
                model_fields = m_props.get("fields", [])

                for field in model_fields:
                    fname = field if isinstance(field, str) else field.get("name", "")
                    fname_lower = fname.lower()

                    # Common drift: id vs custom primary key (e.g. customer_id, account_id)
                    if fname_lower == "id" and "id" not in table_cols:
                        pk_candidates = [c for c in table_cols if c.endswith("_id")]
                        for cand in pk_candidates:
                            results.append(
                                DiscrepancyResult(
                                    title=f"Column Identifier Naming Drift in '{m_name}': 'id' vs '{cand}'",
                                    finding_type=self.detector_type,
                                    severity="medium",
                                    confidence=0.91,
                                    description=(
                                        f"Model '{m_name}' defines field 'id', but table schema '{target_table}' "
                                        f"declares primary key column as '{cand}'."
                                    ),
                                    file_path=m.get("path"),
                                    expected=cand,
                                    actual="id",
                                    related_node_ids=[
                                        nid for nid in [m.get("id"), matched_table.get("id")] if nid
                                    ],
                                    metadata={"field": fname, "expected_column": cand},
                                )
                            )
                    elif fname_lower not in table_cols and fname_lower.endswith(("_id", "_name")):
                        # Check if table has alternative naming (e.g. client_id vs customer_id)
                        for tcol in table_cols:
                            if tcol != fname_lower and (tcol.endswith("_id") and fname_lower.endswith("_id")):
                                results.append(
                                    DiscrepancyResult(
                                        title=f"Foreign Key Column Naming Divergence: '{fname}' vs '{tcol}'",
                                        finding_type=self.detector_type,
                                        severity="low",
                                        confidence=0.85,
                                        description=(
                                            f"Model '{m_name}' specifies attribute '{fname}', whereas schema "
                                            f"table '{target_table}' contains column '{tcol}'."
                                        ),
                                        file_path=m.get("path"),
                                        expected=tcol,
                                        actual=fname,
                                        related_node_ids=[
                                            nid for nid in [m.get("id"), matched_table.get("id")] if nid
                                        ],
                                    )
                                )

        return results
