import json
import uuid
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000/api/v1"

def post(endpoint, data):
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def get(endpoint):
    req = urllib.request.Request(f"{BASE_URL}{endpoint}")
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def patch(endpoint, data):
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="PATCH"
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

print("=== CHECK 1: HEALTH & SYSTEM TELEMETRY ===")
status, res = get("/health")
print("Health:", status, res)
status, res = get("/system/status")
print("System Status:", status, res["data"]["status"], "DB:", res["data"]["database_connected"])
status, res = get("/system/summary")
print("System Summary:", status, "Repos:", res["data"]["repositories_count"])

print("\n=== CHECK 2: PHASE 3 - REALITY GRAPH ===")
files_payload = {
    "repository_name": "ecommerce-core",
    "files": {
        "package.json": json.dumps({"name": "ecommerce-frontend", "version": "1.0.0", "dependencies": {"react": "^18.0.0"}}),
        "docker-compose.yml": "version: '3.8'\nservices:\n  orders:\n    image: orders:latest\n    depends_on:\n      - db\n  db:\n    image: postgres:15",
        "openapi.yaml": "openapi: 3.0.0\ninfo:\n  title: Orders API\n  version: 1.0.0\npaths:\n  /api/v1/orders:\n    get:\n      responses:\n        '200':\n          description: list orders",
        "schema.sql": "CREATE TABLE orders (id INT PRIMARY KEY, total DECIMAL(10,2));",
        "README.md": "# Orders Service\nProvides orders API at /api/v1/orders"
    }
}
status, res = post("/graph/ingest", files_payload)
print("Graph Ingest:", status, "Nodes created:", res["data"]["nodes_count"], "Edges created:", res["data"]["edges_count"])
status, res = get("/graph/statistics")
print("Graph Stats:", status, "Total nodes:", res["data"]["total_nodes"], "Total edges:", res["data"]["total_edges"])
status, graph_data = get("/graph")
print("Graph Retrieval:", status, "Retrieved nodes:", len(graph_data["data"]["nodes"]))

print("\n=== CHECK 3: PHASE 4 - CONTEXT ENGINE ===")
# Create a repository record if needed
status, res = post("/context/analyze", {})
findings_list = res if isinstance(res, list) else res.get("data", [])
print("Context Analyze:", status, "Findings generated:", len(findings_list))
status, findings_res = get("/context/findings")
findings_data = findings_res if isinstance(findings_res, list) else findings_res.get("data", [])
print("Context Findings list:", status, "Count:", len(findings_data))
if findings_data:
    f = findings_data[0]
    print(f"Sample Finding: [{f['severity']}] {f['title']} (Type: {f['finding_type']}) Evidence:", bool(f.get('evidence_payload')))

print("\n=== CHECK 4: PHASE 5 - CHANGE TWIN ===")
diff_payload = {
    "title": "Modify Orders Service API",
    "git_diff": """diff --git a/orders.py b/orders.py
--- a/orders.py
+++ b/orders.py
@@ -1,5 +1,6 @@
-def get_orders():
+def get_orders(customer_id: int):
     pass
""",
    "branch": "feature/customer-orders",
    "author": "dev@mirrorx.local"
}
status, change_res = post("/changes/impact", diff_payload)
change_data = change_res.get("data", change_res)
print("Change Impact:", status, "Risk Score:", change_data.get("risk_score"), "Blast Radius:", change_data.get("total_blast_radius", change_data.get("total_impact_count")))
change_id = change_data.get("id", change_data.get("record_id"))

print("\n=== CHECK 5: PHASE 6 - SYNTHETIC SCENARIO ENGINE ===")
list_status, list_res = get("/scenarios")
print("Existing Scenarios count:", list_status, len(list_res["data"]))
scenario_payload = {
    "target_name": "OrdersAPI",
    "scenario_class": "normal",
    "source_type": "api",
    "seed": 42
}
status, sc_res = post("/scenarios/generate", scenario_payload)
print("Scenario Generate:", status, "ID:", sc_res["data"]["id"], "Class:", sc_res["data"]["scenario_class"])
sc_id = sc_res["data"]["id"]

# Verify seed reproducibility
status, sc_res_2 = post("/scenarios/generate", scenario_payload)
print("Reproducibility check (same seed 42):", sc_res["data"]["generated_inputs"] == sc_res_2["data"]["generated_inputs"])

# Execute scenario
status, exec_res = post(f"/scenarios/{sc_id}/execute", {})
print("Scenario Execution:", status, "Passed:", exec_res["data"]["passed"], "Duration:", exec_res["data"]["execution_duration_ms"], "ms")

print("\n=== CHECK 6: PHASE 7 - AGENT BEHAVIOR LAB ===")
agent_payload = {
    "name": "Audit Test Agent",
    "version": "1.0.0",
    "model_reference": "claude-3-5-sonnet",
    "purpose": "Verify order schema integrity and query latency"
}
status, agent_res = post("/agents", agent_payload)
agent_id = agent_res["data"]["id"]
print("Agent Created:", status, "ID:", agent_id)

# Create Run 1
run_payload_1 = {
    "goal": "Audit order schema performance",
    "context_reference": {"repo": "ecommerce-core"}
}
status, run_1 = post(f"/agents/{agent_id}/run", run_payload_1)
print("Agent Run 1:", status, "Run ID:", run_1["data"]["id"], "Trace ID:", run_1["data"]["trace_id"])
print("Run 1 Behaviors:", {
    "success": run_1["data"]["successful_completion"],
    "correct_tools": run_1["data"]["correct_tool_selection_count"],
    "incorrect_tools": run_1["data"]["incorrect_tool_use_count"],
    "unnecessary_actions": run_1["data"]["unnecessary_actions_count"],
    "policy_violations": run_1["data"]["policy_violations_count"],
    "errors": run_1["data"]["error_count"],
    "latency_ms": run_1["data"]["latency_ms"],
    "retries": run_1["data"]["retry_count"]
})

# Create candidate agent version 1.1.0 and Run 2
agent_payload_2 = {
    "name": "Audit Test Agent v2",
    "version": "1.1.0",
    "model_reference": "claude-3-5-sonnet",
    "purpose": "Optimized verification agent"
}
status, agent_res_2 = post("/agents", agent_payload_2)
agent_id_2 = agent_res_2["data"]["id"]
status, run_2 = post(f"/agents/{agent_id_2}/run", run_payload_1)
print("Agent Run 2:", status, "Run ID:", run_2["data"]["id"])

# Version Comparison
comp_payload = {
    "baseline_run_id": run_1["data"]["id"],
    "candidate_run_id": run_2["data"]["id"]
}
status, comp_res = post("/agents/compare", comp_payload)
print("Version Comparison:", status, "Latency Delta:", comp_res["data"]["behavioral_matrix"]["latency_ms"]["delta"], "Disclaimer:", comp_res["data"]["disclaimer"][:45] + "...")

print("\n=== CHECK 7: PHASE 8 - TRUST LAYER ===")
# Evaluate standard sandbox action -> ALLOW
eval_allow = {
    "principal_name": "test_engineer",
    "resource_name": "sandbox_orders_db",
    "action_name": "read",
    "is_sandbox": True
}
status, allow_res = post("/trust/evaluate", eval_allow)
print("Trust Evaluate (Sandbox Read):", status, "Result:", allow_res["data"]["result"], "(Expected: ALLOW)")

# Evaluate destructive action -> HUMAN_REVIEW_REQUIRED
eval_review = {
    "principal_name": "test_engineer",
    "resource_name": "sandbox_orders_db",
    "action_name": "drop_table",
    "is_sandbox": True
}
status, review_res = post("/trust/evaluate", eval_review)
print("Trust Evaluate (Destructive):", status, "Result:", review_res["data"]["result"], "(Expected: HUMAN_REVIEW_REQUIRED)")

# Evaluate non-sandbox production action -> DENY
eval_deny = {
    "principal_name": "test_engineer",
    "resource_name": "production_orders_db",
    "action_name": "read",
    "is_sandbox": False
}
status, deny_res = post("/trust/evaluate", eval_deny)
print("Trust Evaluate (Production Access):", status, "Result:", deny_res["data"]["result"], "Reason:", deny_res["data"]["reason"], "(Expected: DENY)")

status, dec_list = get("/trust/decisions")
print("Policy Decisions Log count:", status, len(dec_list["data"]))

print("\n=== CHECK 8: PHASE 9 - EVIDENCE LEDGER & RELEASE PASSPORT ===")
# Create Evidence Record
evidence_payload = {
    "evidence_type": "api_contract",
    "source_reference": "repo://ecommerce-core/openapi.yaml",
    "summary": "Verified Orders API v1 specification",
    "raw_payload": {"path": "/api/v1/orders", "method": "GET", "status": 200},
    "confidence": 1.0
}
status, ev_res = post("/evidence", evidence_payload)
print("Evidence Record created:", status, "Hash:", ev_res["data"]["hash_signature"][:16] + "...")

rel_ver = f"1.0.0-rc-{uuid.uuid4().hex[:6]}"
release_payload = {
    "name": f"Release {rel_ver}",
    "version": rel_ver,
    "target_environment": "staging",
    "commit_hash": "a1b2c3d4e5f67890"
}
status, rel_res = post("/releases", release_payload)
rel_id = rel_res["data"]["id"]
print("Release created:", status, "ID:", rel_id, "Version:", rel_res["data"]["version"])

# Issue Release Passport
status, pass_res = post(f"/releases/{rel_id}/passport", {})
print("Release Passport Issued:", status, "Overall Status:", pass_res["data"]["overall_status"])
print("Passport Domains:", {
    "code_changes": pass_res["data"]["code_change_analysis"]["status"],
    "findings": pass_res["data"]["context_findings"]["status"],
    "scenarios": pass_res["data"]["scenario_testing"]["status"],
    "agents": pass_res["data"]["agent_testing"]["status"],
    "policies": pass_res["data"]["policy_validation"]["status"],
    "evidence": pass_res["data"]["evidence_completeness"]["status"]
})
print("Uncertainty Notes:", pass_res["data"]["uncertainty_notes"])
print("Cryptographic Seal:", pass_res["data"]["passport_hash"][:16] + "...")

print("\n=== ALL DIRECT API CHECKS COMPLETE ===")
