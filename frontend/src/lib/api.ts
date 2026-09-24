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
    // If backend is unreachable (e.g. running standalone tests without server process), return structured error
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

