/**
 * API client for MIRROR-X Command Center and backend communication.
 * Connects to FastAPI backend and preserves strict type safety.
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface StandardResponse<T> {
  status: 'success' | 'error';
  data: T;
  meta?: {
    total?: number;
    page?: number;
    limit?: number;
    pages?: number;
    [key: string]: unknown;
  };
}

export interface SystemStatus {
  status: 'healthy' | 'degraded' | 'uninitialized';
  database_connected: boolean;
  database_dialect: string;
  database_latency_ms: number;
  api_version: string;
  uptime_seconds: number;
  timestamp: string;
  active_connections: number;
}

export interface FindingSeverityCounts {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
  total: number;
}

export interface SystemSummary {
  repositories_count: number;
  services_count: number;
  findings_count: number;
  findings_by_severity: FindingSeverityCounts;
  services_healthy_count: number;
  services_degraded_count: number;
  system_status: 'healthy' | 'degraded' | 'uninitialized';
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface Repository {
  id: string;
  name: string;
  url: string;
  default_branch: string;
  language: string | null;
  status: string;
  project_id: string;
  services_count: number;
  findings_count: number;
  created_at: string;
  updated_at: string;
}

export interface Service {
  id: string;
  name: string;
  service_type: string;
  status: 'healthy' | 'degraded' | 'offline';
  runtime: string | null;
  version: string;
  repository_id: string;
  repository_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Finding {
  id: string;
  title: string;
  finding_type: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  confidence: number;
  description: string;
  evidence_payload?: Record<string, unknown> | null;
  status: 'open' | 'resolved' | 'dismissed';
  repository_id?: string | null;
  service_id?: string | null;
  repository_name?: string | null;
  service_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Activity {
  id: string;
  actor: string;
  action: string;
  entity_type: string;
  entity_name: string;
  details?: string | null;
  metadata_payload?: Record<string, unknown> | null;
  created_at: string;
}

export interface CreateRepositoryPayload {
  name: string;
  url: string;
  default_branch?: string;
  language?: string;
  project_id: string;
}

export interface GraphNode {
  id: string;
  node_type:
    | 'repository'
    | 'service'
    | 'component'
    | 'api'
    | 'database'
    | 'table'
    | 'deployment'
    | 'documentation';
  name: string;
  path?: string | null;
  properties: Record<string, unknown>;
  repository_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface GraphEdge {
  id: string;
  relationship_type:
    | 'contains'
    | 'depends_on'
    | 'calls'
    | 'reads_from'
    | 'writes_to'
    | 'deployed_as'
    | 'documents';
  properties: Record<string, unknown>;
  source_node_id: string;
  target_node_id: string;
  source_node_name?: string | null;
  source_node_type?: string | null;
  target_node_name?: string | null;
  target_node_type?: string | null;
  created_at: string;
}

export interface GraphStatistics {
  total_nodes: number;
  total_edges: number;
  nodes_by_type: Record<string, number>;
  edges_by_relationship: Record<string, number>;
  graph_density: number;
}

export interface GraphRetrieval {
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_nodes: number;
  total_edges: number;
}

async function fetchFromApi<T>(endpoint: string, options?: RequestInit): Promise<StandardResponse<T>> {
  try {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    });

    if (!res.ok) {
      throw new Error(`API error ${res.status}: ${res.statusText}`);
    }

    const json = await res.json();
    if (json && typeof json === 'object' && !Array.isArray(json) && 'data' in json && 'status' in json) {
      return json as StandardResponse<T>;
    }
    return {
      status: 'success',
      data: json as T,
    };
  } catch (err) {
    throw err;
  }
}

export async function getSystemStatus(): Promise<SystemStatus> {
  const resp = await fetchFromApi<SystemStatus>('/system/status');
  return resp.data;
}

export async function getSystemSummary(): Promise<SystemSummary> {
  const resp = await fetchFromApi<SystemSummary>('/system/summary');
  return resp.data;
}

export async function getRepositories(search?: string): Promise<{ items: Repository[]; total: number }> {
  const query = search ? `?search=${encodeURIComponent(search)}` : '';
  const resp = await fetchFromApi<Repository[]>(`/repositories${query}`);
  return {
    items: resp.data,
    total: resp.meta?.total ?? resp.data.length,
  };
}

export async function getServices(status?: string, search?: string): Promise<{ items: Service[]; total: number }> {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (search) params.set('search', search);
  const query = params.toString() ? `?${params.toString()}` : '';
  const resp = await fetchFromApi<Service[]>(`/services${query}`);
  return {
    items: resp.data,
    total: resp.meta?.total ?? resp.data.length,
  };
}

export async function getFindings(severity?: string): Promise<{ items: Finding[]; total: number }> {
  const query = severity ? `?severity=${encodeURIComponent(severity)}` : '';
  const resp = await fetchFromApi<Finding[]>(`/findings${query}`);
  return {
    items: resp.data,
    total: resp.meta?.total ?? resp.data.length,
  };
}

export async function getFindingsSummary(): Promise<FindingSeverityCounts> {
  const resp = await fetchFromApi<FindingSeverityCounts>('/findings/summary');
  return resp.data;
}

export async function getActivities(limit = 15): Promise<Activity[]> {
  const resp = await fetchFromApi<Activity[]>(`/activities?limit=${limit}`);
  return resp.data;
}

export async function createRepository(payload: CreateRepositoryPayload): Promise<Repository> {
  const resp = await fetchFromApi<Repository>('/repositories', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return resp.data;
}

export async function getGraph(params?: {
  repository_id?: string;
  node_type?: string;
  search?: string;
}): Promise<GraphRetrieval> {
  const q = new URLSearchParams();
  if (params?.repository_id) q.set('repository_id', params.repository_id);
  if (params?.node_type) q.set('node_type', params.node_type);
  if (params?.search) q.set('search', params.search);
  const queryStr = q.toString() ? `?${q.toString()}` : '';
  const resp = await fetchFromApi<GraphRetrieval>(`/graph${queryStr}`);
  return resp.data;
}

export async function getGraphStatistics(): Promise<GraphStatistics> {
  const resp = await fetchFromApi<GraphStatistics>('/graph/statistics');
  return resp.data;
}

export async function getNodeDetails(nodeId: string): Promise<GraphNode> {
  const resp = await fetchFromApi<GraphNode>(`/graph/nodes/${nodeId}`);
  return resp.data;
}

export async function ingestRepository(payload: {
  repository_name: string;
  repository_id?: string;
  files: Record<string, string>;
}): Promise<{ repository: string; nodes_count: number; edges_count: number; warnings_count: number }> {
  const resp = await fetchFromApi<{
    repository: string;
    nodes_count: number;
    edges_count: number;
    warnings_count: number;
  }>('/graph/ingest', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return resp.data;
}

export interface ContextStatistics {
  total_findings: number;
  findings_by_type: Record<string, number>;
  findings_by_severity: Record<string, number>;
  findings_by_status: Record<string, number>;
  resolution_rate: number;
}

export interface FindingDetailResponse {
  finding: Finding;
  related_nodes: Array<{
    id: string;
    name: string;
    node_type: string;
    path?: string;
    properties?: Record<string, unknown>;
  }>;
}

export async function analyzeContext(payload?: {
  repository_id?: string;
  file_tree?: Record<string, string>;
}): Promise<Finding[]> {
  const resp = await fetchFromApi<Finding[]>('/context/analyze', {
    method: 'POST',
    body: JSON.stringify(payload || {}),
  });
  return resp.data;
}

export async function getContextFindings(params?: {
  finding_type?: string;
  severity?: string;
  status?: string;
  repository_id?: string;
  skip?: number;
  limit?: number;
}): Promise<Finding[]> {
  const q = new URLSearchParams();
  if (params?.finding_type) q.set('finding_type', params.finding_type);
  if (params?.severity) q.set('severity', params.severity);
  if (params?.status) q.set('status', params.status);
  if (params?.repository_id) q.set('repository_id', params.repository_id);
  if (params?.skip !== undefined) q.set('skip', params.skip.toString());
  if (params?.limit !== undefined) q.set('limit', params.limit.toString());
  const queryStr = q.toString() ? `?${q.toString()}` : '';
  const resp = await fetchFromApi<Finding[]>(`/context/findings${queryStr}`);
  return resp.data;
}

export async function getContextFindingDetail(findingId: string): Promise<FindingDetailResponse> {
  const resp = await fetchFromApi<FindingDetailResponse>(`/context/findings/${findingId}`);
  return resp.data;
}

export async function updateFindingStatus(findingId: string, status: string): Promise<Finding> {
  const resp = await fetchFromApi<Finding>(`/context/findings/${findingId}`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
  return resp.data;
}

export async function getContextStatistics(repositoryId?: string): Promise<ContextStatistics> {
  const q = repositoryId ? `?repository_id=${repositoryId}` : '';
  const resp = await fetchFromApi<ContextStatistics>(`/context/statistics${q}`);
  return resp.data;
}

export interface ImpactNodeItem {
  node_id: string;
  name: string;
  node_type: string;
  path?: string;
  reason: string;
  depth?: number;
  propagation_path?: string[];
  properties?: Record<string, unknown>;
}

export interface ChangeImpactAnalysisResult {
  record_id: string;
  title: string;
  branch?: string;
  author?: string;
  direct_impact_count: number;
  indirect_impact_count: number;
  total_impacted_nodes: number;
  risk_score: number;
  risk_level: 'critical' | 'high' | 'medium' | 'low';
  affected_categories: Record<string, number>;
  breaking_changes: Array<{
    title: string;
    severity: string;
    source_node: string;
    impacted_nodes: string[];
    description: string;
  }>;
  direct_nodes: ImpactNodeItem[];
  indirect_nodes: ImpactNodeItem[];
  modified_files: Array<{
    file_path: string;
    change_type: string;
    additions: number;
    deletions: number;
  }>;
}

export interface ChangeRecord {
  id: string;
  title: string;
  branch?: string;
  author?: string;
  git_diff: string;
  direct_impact_count: number;
  indirect_impact_count: number;
  risk_score: number;
  risk_level: string;
  impact_summary: Record<string, unknown>;
  repository_id?: string;
  created_at: string;
  updated_at: string;
}

export async function analyzeChangeImpact(payload: {
  title: string;
  git_diff: string;
  repository_id?: string;
  branch?: string;
  author?: string;
}): Promise<ChangeImpactAnalysisResult> {
  const resp = await fetchFromApi<ChangeImpactAnalysisResult>('/changes/impact', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return resp.data;
}

export async function getChangeRecords(repository_id?: string): Promise<ChangeRecord[]> {
  const q = repository_id ? `?repository_id=${repository_id}` : '';
  const resp = await fetchFromApi<ChangeRecord[]>(`/changes${q}`);
  return resp.data;
}

/* =========================================================================
   PHASE 6: SYNTHETIC SCENARIOS
   ========================================================================= */

export interface Scenario {
  id: string;
  name: string;
  scenario_class:
    | 'normal'
    | 'boundary'
    | 'incomplete'
    | 'malformed'
    | 'contradictory'
    | 'unauthorized'
    | 'adversarial'
    | 'outage'
    | 'tool_failure'
    | 'ambiguous';
  source_type: string;
  seed: number;
  initial_state: Record<string, unknown>;
  generated_inputs: Record<string, unknown>;
  expected_constraints: Record<string, unknown>;
  participating_resources: Array<{ name: string; type: string; role: string }>;
  applicable_policies: Array<{ id: string; name: string; enforcement: string }>;
  metadata_payload: Record<string, unknown>;
  status: string;
  execution_result?: {
    execution_id: string;
    passed: boolean;
    actual_status: number;
    actual_decision: string;
    execution_duration_ms: number;
  } | null;
  created_at: string;
  updated_at: string;
}

export async function generateScenario(payload: {
  target_name: string;
  source_type?: string;
  scenario_class?: string;
  seed?: number;
  parameters?: Record<string, unknown>;
}): Promise<Scenario> {
  const resp = await fetchFromApi<Scenario>('/scenarios/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return resp.data;
}

export async function getScenarios(params?: {
  scenario_class?: string;
  source_type?: string;
}): Promise<Scenario[]> {
  const q = new URLSearchParams();
  if (params?.scenario_class) q.set('scenario_class', params.scenario_class);
  if (params?.source_type) q.set('source_type', params.source_type);
  const queryStr = q.toString() ? `?${q.toString()}` : '';
  const resp = await fetchFromApi<Scenario[]>(`/scenarios${queryStr}`);
  return resp.data;
}

export async function executeScenario(scenarioId: string): Promise<Record<string, unknown>> {
  const resp = await fetchFromApi<Record<string, unknown>>(`/scenarios/${scenarioId}/execute`, {
    method: 'POST',
  });
  return resp.data;
}

export async function generateBatchScenarios(targetName = 'CheckoutService', seed = 42): Promise<Scenario[]> {
  const resp = await fetchFromApi<Scenario[]>(`/scenarios/batch?target_name=${encodeURIComponent(targetName)}&seed=${seed}`, {
    method: 'POST',
  });
  return resp.data;
}

/* =========================================================================
   PHASE 7: AGENT BEHAVIOR LAB
   ========================================================================= */

export interface Agent {
  id: string;
  name: string;
  version: string;
  model_reference: string;
  purpose: string;
  status: string;
  config_payload: Record<string, unknown>;
  created_at: string;
}

export interface AgentStep {
  id: string;
  step_number: number;
  thought: string;
  tool_call?: string | null;
  arguments: Record<string, unknown>;
  tool_output?: Record<string, unknown> | null;
  policy_check: { decision: string; policy?: string; reason?: string };
  duration_ms: number;
  status: string;
  error?: string | null;
}

export interface AgentRun {
  id: string;
  agent_id: string;
  agent_version: string;
  goal: string;
  context_reference: Record<string, unknown>;
  model_reference: string;
  trace_id: string;
  plan: string[];
  status: string;
  result?: { output: string; steps_count: number; success: boolean } | null;
  errors: string[];
  timings: { total_duration_ms: number; planning_ms: number; execution_ms: number };
  successful_completion: boolean;
  correct_tool_selection_count: number;
  incorrect_tool_use_count: number;
  unnecessary_actions_count: number;
  policy_violations_count: number;
  error_count: number;
  latency_ms: number;
  retry_count: number;
  steps: AgentStep[];
  created_at: string;
}

export interface AgentCompareResult {
  baseline_version: string;
  candidate_version: string;
  baseline_trace_id?: string;
  candidate_trace_id?: string;
  behavioral_matrix: {
    successful_completion: { baseline: boolean; candidate: boolean; improved: boolean; regressed: boolean };
    correct_tool_selection: { baseline: number; candidate: number; delta: number; improved: boolean };
    incorrect_tool_use: { baseline: number; candidate: number; delta: number; improved: boolean };
    unnecessary_actions: { baseline: number; candidate: number; delta: number; improved: boolean };
    policy_violations: { baseline: number; candidate: number; delta: number; improved: boolean };
    error_count: { baseline: number; candidate: number; delta: number; improved: boolean };
    latency_ms: { baseline: number; candidate: number; delta: number; improved: boolean };
    retry_count: { baseline: number; candidate: number; delta: number; improved: boolean };
  };
  disclaimer: string;
}

export async function getAgents(): Promise<Agent[]> {
  const resp = await fetchFromApi<Agent[]>('/agents');
  return resp.data;
}

export async function createAgent(payload: {
  name: string;
  version: string;
  model_reference: string;
  purpose: string;
}): Promise<Agent> {
  const resp = await fetchFromApi<Agent>('/agents', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return resp.data;
}

export async function getAgentTools(): Promise<Array<{ name: string; description: string; risk_level: string; is_mock_safe: boolean }>> {
  const resp = await fetchFromApi<Array<{ name: string; description: string; risk_level: string; is_mock_safe: boolean }>>('/agents/tools');
  return resp.data;
}

export async function runAgent(agentId: string, payload: { goal: string }): Promise<AgentRun> {
  const resp = await fetchFromApi<AgentRun>(`/agents/${agentId}/run`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return resp.data;
}

export async function getAgentRuns(agentId?: string): Promise<AgentRun[]> {
  const q = agentId ? `?agent_id=${agentId}` : '';
  const resp = await fetchFromApi<AgentRun[]>(`/agents/runs/list${q}`);
  return resp.data;
}

export async function compareAgentRuns(baselineRunId: string, candidateRunId: string): Promise<AgentCompareResult> {
  const resp = await fetchFromApi<AgentCompareResult>('/agents/compare', {
    method: 'POST',
    body: JSON.stringify({ baseline_run_id: baselineRunId, candidate_run_id: candidateRunId }),
  });
  return resp.data;
}

/* =========================================================================
   PHASE 8: TRUST LAYER
   ========================================================================= */

export interface TrustPolicy {
  id?: string;
  name: string;
  description: string;
  enforcement_level: string;
  target_type: string;
  rules_payload: Record<string, unknown>;
  is_active: boolean;
}

export interface PermissionItem {
  id?: string;
  name: string;
  principal_role: string;
  resource_type: string;
  action_name: string;
  effect: 'ALLOW' | 'DENY';
}

export interface TrustResourceItem {
  name: string;
  resource_type: string;
  classification: string;
  is_sandbox: boolean;
}

export interface PolicyDecisionItem {
  id: string;
  principal_name: string;
  agent_name?: string | null;
  tool_name?: string | null;
  resource_name: string;
  action_name: string;
  result: 'ALLOW' | 'DENY' | 'HUMAN_REVIEW_REQUIRED';
  reason: string;
  matched_policies: string[];
  evidence_id?: string | null;
  reviewed_by?: string | null;
  review_status?: string | null;
  created_at: string;
}

export async function getTrustPolicies(): Promise<TrustPolicy[]> {
  const resp = await fetchFromApi<TrustPolicy[]>('/trust/policies');
  return resp.data;
}

export async function getTrustPermissions(): Promise<PermissionItem[]> {
  const resp = await fetchFromApi<PermissionItem[]>('/trust/permissions');
  return resp.data;
}

export async function getTrustResources(): Promise<TrustResourceItem[]> {
  const resp = await fetchFromApi<TrustResourceItem[]>('/trust/resources');
  return resp.data;
}

export async function evaluateTrustPolicy(payload: {
  principal_name: string;
  resource_name: string;
  action_name: string;
  agent_name?: string;
  resource_classification?: string;
  is_sandbox?: boolean;
}): Promise<{
  result: 'ALLOW' | 'DENY' | 'HUMAN_REVIEW_REQUIRED';
  reason: string;
  matched_policies: string[];
  evidence?: Record<string, unknown> | null;
  is_sandbox: boolean;
}> {
  const resp = await fetchFromApi<{
    result: 'ALLOW' | 'DENY' | 'HUMAN_REVIEW_REQUIRED';
    reason: string;
    matched_policies: string[];
    evidence?: Record<string, unknown> | null;
    is_sandbox: boolean;
  }>('/trust/evaluate', {
    method: 'POST',
    body: JSON.stringify({ is_sandbox: true, ...payload }),
  });
  return resp.data;
}

export async function getPolicyDecisions(resultFilter?: string): Promise<PolicyDecisionItem[]> {
  const q = resultFilter ? `?result_filter=${encodeURIComponent(resultFilter)}` : '';
  const resp = await fetchFromApi<PolicyDecisionItem[]>(`/trust/decisions${q}`);
  return resp.data;
}

export async function reviewPolicyDecision(decisionId: string, reviewStatus: 'approved' | 'rejected', reviewedBy: string): Promise<PolicyDecisionItem> {
  const resp = await fetchFromApi<PolicyDecisionItem>(`/trust/decisions/${decisionId}/review`, {
    method: 'POST',
    body: JSON.stringify({ review_status: reviewStatus, reviewed_by: reviewedBy }),
  });
  return resp.data;
}

/* =========================================================================
   PHASE 9: EVIDENCE LEDGER & RELEASE PASSPORT
   ========================================================================= */

export interface EvidenceItem {
  id: string;
  evidence_type:
    | 'source_file'
    | 'graph_relationship'
    | 'api_contract'
    | 'test_execution'
    | 'scenario_run'
    | 'agent_execution'
    | 'policy_decision'
    | 'runtime_trace';
  source_reference: string;
  summary: string;
  raw_payload: Record<string, unknown>;
  hash_signature: string;
  confidence: number;
  linked_finding_id?: string | null;
  created_at: string;
}

export interface ReleaseItem {
  id: string;
  name: string;
  version: string;
  target_environment: string;
  commit_hash: string;
  change_ids: string[];
  status: string;
  created_at: string;
}

export interface ReleasePassportItem {
  id: string;
  release_id: string;
  overall_status: 'PASS' | 'FAIL' | 'WARNING' | 'HUMAN_REVIEW_REQUIRED' | 'NOT_EVALUATED';
  code_change_analysis: {
    status: string;
    total_changes: number;
    breaking_changes_count: number;
    max_risk_score: number;
  };
  context_findings: {
    status: string;
    total_findings: number;
    open_findings: number;
    critical_count: number;
    high_count: number;
  };
  scenario_testing: {
    status: string;
    total_scenarios: number;
    passed_count: number;
    failed_count: number;
    classes_tested: string[];
  };
  agent_testing: {
    status: string;
    total_runs: number;
    policy_violations: number;
    evaluated_models: string[];
  };
  policy_validation: {
    status: string;
    total_evaluations: number;
    denied_count: number;
    review_required_count: number;
  };
  evidence_completeness: {
    status: string;
    total_evidence_records: number;
    completeness_score: number;
  };
  uncertainty_notes: string;
  passport_hash: string;
  created_at: string;
}

export async function getEvidenceList(typeFilter?: string, search?: string): Promise<EvidenceItem[]> {
  const q = new URLSearchParams();
  if (typeFilter) q.set('evidence_type', typeFilter);
  if (search) q.set('search', search);
  const queryStr = q.toString() ? `?${q.toString()}` : '';
  const resp = await fetchFromApi<EvidenceItem[]>(`/evidence${queryStr}`);
  return resp.data;
}

export async function getEvidence(evidenceId: string): Promise<EvidenceItem> {
  const resp = await fetchFromApi<EvidenceItem>(`/evidence/${evidenceId}`);
  return resp.data;
}

export async function createEvidence(payload: {
  evidence_type: string;
  source_reference: string;
  summary: string;
  raw_payload: Record<string, unknown>;
  confidence?: number;
  linked_finding_id?: string | null;
  linked_change_id?: string | null;
}): Promise<EvidenceItem> {
  const resp = await fetchFromApi<EvidenceItem>('/evidence', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return resp.data;
}

export async function getReleases(): Promise<ReleaseItem[]> {
  const resp = await fetchFromApi<ReleaseItem[]>('/releases');
  return resp.data;
}

export async function createRelease(payload: {
  name: string;
  version: string;
  target_environment?: string;
  commit_hash: string;
}): Promise<ReleaseItem> {
  const resp = await fetchFromApi<ReleaseItem>('/releases', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return resp.data;
}

export async function getReleasePassport(releaseId: string): Promise<ReleasePassportItem> {
  const resp = await fetchFromApi<ReleasePassportItem>(`/releases/${releaseId}/passport`);
  return resp.data;
}

export async function issueReleasePassport(releaseId: string): Promise<ReleasePassportItem> {
  const resp = await fetchFromApi<ReleasePassportItem>(`/releases/${releaseId}/passport`, {
    method: 'POST',
  });
  return resp.data;
}
