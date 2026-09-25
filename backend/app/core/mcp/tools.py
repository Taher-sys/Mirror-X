"""Implementation of the 10 controlled Model Context Protocol (MCP) tools."""

import time
import uuid
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai.agent_lab_evaluator import AgentLabEvaluator
from app.core.changes.impact_engine import ChangeImpactEngine
from app.core.config import get_settings
from app.core.mcp.types import MCPToolDefinition
from app.core.releases.passport_engine import ReleasePassportEngine
from app.core.scenarios.generator import SyntheticScenarioEngine
from app.core.security.sanitizer import sanitize_secrets
from app.core.trust.engine import TrustLayerEngine
from app.models.evidence import EvidenceRecord
from app.models.finding import Finding
from app.models.graph import GraphEdge, GraphNode
from app.models.repository import Repository
from app.models.scenario import ScenarioRecord
from app.models.service import Service
from app.models.trust import PolicyDecision

settings = get_settings()

# Tool Definitions Specifications
MCP_TOOL_DEFINITIONS: list[MCPToolDefinition] = [
    MCPToolDefinition(
        name="inspect_system",
        description="Inspect MIRROR-X system status, health, and aggregate metric summaries.",
        inputSchema={
            "type": "object",
            "properties": {
                "include_metrics": {
                    "type": "boolean",
                    "description": "Whether to include high-level entity counts.",
                    "default": True,
                },
            },
        },
        required_permission="system:read",
    ),
    MCPToolDefinition(
        name="query_reality_graph",
        description="Query nodes and relationships in the Reality Graph with optional filters.",
        inputSchema={
            "type": "object",
            "properties": {
                "repository_id": {"type": "string", "description": "Optional repository UUID."},
                "node_type": {"type": "string", "description": "Filter by node type (service, database, etc.)."},
                "search": {"type": "string", "description": "Search term matching node name."},
                "limit": {"type": "integer", "default": 50, "description": "Maximum nodes to return."},
            },
        },
        required_permission="graph:read",
    ),
    MCPToolDefinition(
        name="find_context_drift",
        description="Detect discrepancies and drifts between architecture documentation and actual implementations.",
        inputSchema={
            "type": "object",
            "properties": {
                "repository_id": {"type": "string", "description": "Optional repository UUID."},
                "severity": {"type": "string", "description": "Filter by severity (critical, high, medium, low)."},
                "limit": {"type": "integer", "default": 50, "description": "Maximum findings to return."},
            },
        },
        required_permission="system:read",
    ),
    MCPToolDefinition(
        name="analyze_change",
        description="Perform change twin blast-radius and impact analysis on proposed file modifications.",
        inputSchema={
            "type": "object",
            "properties": {
                "files_changed": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of modified file paths.",
                },
                "diff_content": {
                    "type": "string",
                    "description": "Optional unified git diff string.",
                },
            },
            "required": ["files_changed"],
        },
        required_permission="graph:read",
    ),
    MCPToolDefinition(
        name="generate_scenario",
        description="Deterministically synthesize a reproducible test scenario for a service across 10 invariant classes.",
        inputSchema={
            "type": "object",
            "properties": {
                "target_name": {"type": "string", "description": "Name of the target service under test."},
                "scenario_class": {
                    "type": "string",
                    "description": "Scenario class: normal, boundary, incomplete, malformed, contradictory, unauthorized, adversarial, outage, tool_failure, ambiguous.",
                    "default": "normal",
                },
                "source_type": {"type": "string", "default": "api", "description": "Source type."},
                "seed": {"type": "integer", "default": 42, "description": "Deterministic seed."},
            },
            "required": ["target_name"],
        },
        required_permission="scenario:create",
    ),
    MCPToolDefinition(
        name="run_scenario",
        description="Execute a synthetic scenario inside the secure sandbox verification harness.",
        inputSchema={
            "type": "object",
            "properties": {
                "scenario_id": {"type": "string", "description": "UUID of the scenario to execute."},
            },
            "required": ["scenario_id"],
        },
        required_permission="scenario:run",
    ),
    MCPToolDefinition(
        name="inspect_agent_run",
        description="Retrieve execution telemetry, tool sequence, and AI behavioral anomaly analysis for an agent run.",
        inputSchema={
            "type": "object",
            "properties": {
                "run_id": {"type": "string", "description": "UUID of the AgentRun to inspect."},
            },
            "required": ["run_id"],
        },
        required_permission="agent:read",
    ),
    MCPToolDefinition(
        name="check_policy",
        description="Evaluate an action or tool call against Trust Layer policies to determine ALLOW, DENY, or HUMAN_REVIEW_REQUIRED.",
        inputSchema={
            "type": "object",
            "properties": {
                "principal_name": {"type": "string", "description": "Name of principal or agent requesting access."},
                "resource_name": {"type": "string", "description": "Target resource identifier."},
                "action_name": {
                    "type": "string",
                    "description": "Action (read, write, delete, invoke, drop_table, etc.).",
                },
                "is_sandbox": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether the target is sandbox-isolated.",
                },
            },
            "required": ["principal_name", "resource_name", "action_name"],
        },
        required_permission="policy:evaluate",
    ),
    MCPToolDefinition(
        name="search_evidence",
        description="Search cryptographic evidence records in the Evidence Ledger by hash, type, or query.",
        inputSchema={
            "type": "object",
            "properties": {
                "evidence_type": {"type": "string", "description": "Filter by evidence type."},
                "query": {"type": "string", "description": "Search term matching source reference or summary."},
                "limit": {"type": "integer", "default": 20, "description": "Maximum records to return."},
            },
        },
        required_permission="evidence:read",
    ),
    MCPToolDefinition(
        name="generate_release_passport",
        description="Synthesize a multi-domain cryptographic Release Passport assessing release candidate readiness.",
        inputSchema={
            "type": "object",
            "properties": {
                "release_version": {
                    "type": "string",
                    "description": "Release candidate version string (e.g., v1.2.0).",
                },
            },
            "required": ["release_version"],
        },
        required_permission="release:review",
    ),
]


class MCPToolHandlers:
    """Implementations for all 10 MCP tools."""

    @staticmethod
    async def inspect_system(db: AsyncSession, args: dict[str, Any]) -> dict[str, Any]:
        t0 = time.perf_counter()
        try:
            await db.execute(text("SELECT 1"))
            db_connected = True
        except Exception:
            db_connected = False

        repo_res = await db.execute(select(func.count(Repository.id)))
        repo_count = repo_res.scalar() or 0

        svc_res = await db.execute(select(func.count(Service.id)))
        svc_count = svc_res.scalar() or 0

        finding_res = await db.execute(select(func.count(Finding.id)))
        finding_count = finding_res.scalar() or 0

        return {
            "status": "healthy" if db_connected else "degraded",
            "database_connected": db_connected,
            "database_latency_ms": round((time.perf_counter() - t0) * 1000, 2),
            "app_version": settings.app_version,
            "environment": settings.environment,
            "repositories_count": repo_count,
            "services_count": svc_count,
            "findings_count": finding_count,
        }

    @staticmethod
    async def query_reality_graph(db: AsyncSession, args: dict[str, Any]) -> dict[str, Any]:
        query = select(GraphNode)
        repo_id_str = args.get("repository_id")
        if repo_id_str:
            try:
                query = query.where(GraphNode.repository_id == uuid.UUID(repo_id_str))
            except ValueError:
                pass

        node_type = args.get("node_type")
        if node_type:
            query = query.where(GraphNode.node_type == node_type.lower())

        search = args.get("search")
        if search:
            query = query.where(GraphNode.name.ilike(f"%{search}%"))

        limit = min(args.get("limit", 50), 100)
        query = query.limit(limit)

        node_res = await db.execute(query)
        nodes = list(node_res.scalars().all())
        node_ids = {n.id for n in nodes}

        edges = []
        if node_ids:
            edge_query = (
                select(GraphEdge)
                .where((GraphEdge.source_node_id.in_(node_ids)) & (GraphEdge.target_node_id.in_(node_ids)))
                .limit(100)
            )
            edge_res = await db.execute(edge_query)
            edges = list(edge_res.scalars().all())

        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "nodes": [
                {
                    "id": str(n.id),
                    "name": n.name,
                    "node_type": n.node_type,
                    "path": n.path,
                    "properties": sanitize_secrets(n.properties or {}),
                }
                for n in nodes
            ],
            "edges": [
                {
                    "id": str(e.id),
                    "source_id": str(e.source_node_id),
                    "target_id": str(e.target_node_id),
                    "relationship_type": e.relationship_type,
                }
                for e in edges
            ],
        }

    @staticmethod
    async def find_context_drift(db: AsyncSession, args: dict[str, Any]) -> dict[str, Any]:
        query = select(Finding)
        repo_id_str = args.get("repository_id")
        if repo_id_str:
            try:
                query = query.where(Finding.repository_id == uuid.UUID(repo_id_str))
            except ValueError:
                pass

        severity = args.get("severity")
        if severity:
            query = query.where(Finding.severity == severity.lower())

        limit = min(args.get("limit", 50), 100)
        query = query.order_by(Finding.created_at.desc()).limit(limit)

        res = await db.execute(query)
        findings = list(res.scalars().all())

        return {
            "total_findings": len(findings),
            "findings": [
                {
                    "id": str(f.id),
                    "title": f.title,
                    "category": f.category,
                    "severity": f.severity,
                    "status": f.status,
                    "description": f.description,
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                }
                for f in findings
            ],
        }

    @staticmethod
    async def analyze_change(db: AsyncSession, args: dict[str, Any]) -> dict[str, Any]:
        files_changed = args.get("files_changed", [])
        diff_content = args.get("diff_content")
        if not diff_content:
            diff_content = "\n".join(f"--- a/{f}\n+++ b/{f}\n@@ -1,1 +1,2 @@\n+// change in {f}" for f in files_changed)

        # Fetch current reality graph nodes and edges
        node_res = await db.execute(select(GraphNode))
        nodes = list(node_res.scalars().all())

        edge_res = await db.execute(select(GraphEdge))
        edges = list(edge_res.scalars().all())

        nodes_data = [
            {
                "id": str(n.id),
                "name": n.name,
                "node_type": n.node_type,
                "path": n.path,
                "properties": n.properties or {},
            }
            for n in nodes
        ]
        edges_data = [
            {
                "id": str(e.id),
                "source_node_id": str(e.source_node_id),
                "target_node_id": str(e.target_node_id),
                "relationship_type": e.relationship_type,
                "properties": e.properties or {},
            }
            for e in edges
        ]

        engine = ChangeImpactEngine()
        analysis = engine.analyze(diff_text=diff_content, nodes=nodes_data, edges=edges_data)
        return analysis.to_dict()

    @staticmethod
    async def generate_scenario(db: AsyncSession, args: dict[str, Any]) -> dict[str, Any]:
        target_name = args["target_name"]
        scenario_class = args.get("scenario_class", "normal")
        source_type = args.get("source_type", "api")
        seed = args.get("seed", 42)

        engine = SyntheticScenarioEngine(seed=seed)
        data = engine.generate(
            target_name=target_name,
            source_type=source_type,
            scenario_class=scenario_class,
            seed=seed,
        )

        record = ScenarioRecord(
            name=data["name"],
            scenario_class=data["scenario_class"],
            source_type=data["source_type"],
            seed=data["seed"],
            initial_state=data["initial_state"],
            generated_inputs=data["generated_inputs"],
            expected_constraints=data["expected_constraints"],
            participating_resources=data["participating_resources"],
            applicable_policies=data["applicable_policies"],
            metadata_payload=data["metadata"],
            status="generated",
        )
        db.add(record)
        await db.flush()
        await db.refresh(record)

        return {
            "scenario_id": str(record.id),
            "name": record.name,
            "scenario_class": record.scenario_class,
            "seed": record.seed,
            "status": record.status,
            "constraints": record.expected_constraints,
        }

    @staticmethod
    async def run_scenario(db: AsyncSession, args: dict[str, Any]) -> dict[str, Any]:
        scenario_id_str = args["scenario_id"]
        try:
            scenario_uuid = uuid.UUID(scenario_id_str)
        except ValueError:
            raise ValueError(f"Invalid UUID: '{scenario_id_str}'")

        query = select(ScenarioRecord).where(ScenarioRecord.id == scenario_uuid)
        res = await db.execute(query)
        scenario = res.scalar_one_or_none()
        if not scenario:
            raise ValueError(f"Scenario '{scenario_id_str}' not found.")

        engine = SyntheticScenarioEngine(seed=scenario.seed)
        exec_res = engine.execute_scenario(
            {
                "scenario_id": str(scenario.id),
                "scenario_class": scenario.scenario_class,
                "expected_constraints": scenario.expected_constraints,
            }
        )

        scenario.status = "passed" if exec_res["passed"] else "failed"
        scenario.execution_result = exec_res
        await db.flush()

        return exec_res

    @staticmethod
    async def inspect_agent_run(db: AsyncSession, args: dict[str, Any]) -> dict[str, Any]:
        run_id_str = args["run_id"]
        try:
            run_uuid = uuid.UUID(run_id_str)
        except ValueError:
            raise ValueError(f"Invalid UUID: '{run_id_str}'")

        evaluator = AgentLabEvaluator()
        analysis = await evaluator.evaluate_run(db=db, run_id=run_uuid, create_evidence=False)
        return analysis.model_dump()

    @staticmethod
    async def check_policy(db: AsyncSession, args: dict[str, Any]) -> dict[str, Any]:
        engine = TrustLayerEngine()
        result = engine.evaluate(
            principal_name=args["principal_name"],
            resource_name=args["resource_name"],
            action_name=args["action_name"],
            is_sandbox=args.get("is_sandbox", True),
        )

        # Log policy decision to database
        decision = PolicyDecision(
            principal_name=args["principal_name"],
            resource_name=args["resource_name"],
            action_name=args["action_name"],
            result=result["result"],
            reason=result["reason"],
            matched_policies=result.get("matched_policies", []),
            context_snapshot={"is_sandbox": args.get("is_sandbox", True)},
        )
        db.add(decision)
        await db.flush()

        return result

    @staticmethod
    async def search_evidence(db: AsyncSession, args: dict[str, Any]) -> dict[str, Any]:
        query = select(EvidenceRecord)
        ev_type = args.get("evidence_type")
        if ev_type:
            query = query.where(EvidenceRecord.evidence_type == ev_type)

        search_query = args.get("query")
        if search_query:
            query = query.where(
                (EvidenceRecord.source_reference.ilike(f"%{search_query}%"))
                | (EvidenceRecord.summary.ilike(f"%{search_query}%"))
            )

        limit = min(args.get("limit", 20), 50)
        query = query.order_by(EvidenceRecord.created_at.desc()).limit(limit)

        res = await db.execute(query)
        records = list(res.scalars().all())

        return {
            "total_records": len(records),
            "evidence": [
                {
                    "id": str(r.id),
                    "evidence_type": r.evidence_type,
                    "source_reference": r.source_reference,
                    "summary": r.summary,
                    "hash_signature": r.hash_signature,
                    "confidence": r.confidence,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in records
            ],
        }

    @staticmethod
    async def generate_release_passport(db: AsyncSession, args: dict[str, Any]) -> dict[str, Any]:
        release_version = args["release_version"]
        passport_data = ReleasePassportEngine.generate_passport(
            release_version=release_version,
            changes=[],
            findings=[],
            scenarios=[],
            agent_runs=[],
            policy_decisions=[],
            evidence_records=[],
        )
        return passport_data
