import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import DashboardPage from './page';
import * as api from '@/lib/api';

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
  usePathname: () => '/dashboard',
}));

vi.mock('@/lib/api', () => ({
  getSystemStatus: vi.fn(),
  getSystemSummary: vi.fn(),
  getRepositories: vi.fn(),
  getServices: vi.fn(),
  getFindings: vi.fn(),
  getFindingsSummary: vi.fn(),
  getActivities: vi.fn(),
  createRepository: vi.fn(),
}));

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the command center control room header and empty states', async () => {
    vi.mocked(api.getSystemStatus).mockResolvedValue({
      status: 'uninitialized',
      database_connected: true,
      database_dialect: 'sqlite',
      database_latency_ms: 1.2,
      api_version: '0.1.0',
      uptime_seconds: 42.0,
      timestamp: new Date().toISOString(),
      active_connections: 1,
    });
    vi.mocked(api.getSystemSummary).mockResolvedValue({
      repositories_count: 0,
      services_count: 0,
      findings_count: 0,
      findings_by_severity: { critical: 0, high: 0, medium: 0, low: 0, info: 0, total: 0 },
      services_healthy_count: 0,
      services_degraded_count: 0,
      system_status: 'uninitialized',
      timestamp: new Date().toISOString(),
    });
    vi.mocked(api.getRepositories).mockResolvedValue({ items: [], total: 0 });
    vi.mocked(api.getServices).mockResolvedValue({ items: [], total: 0 });
    vi.mocked(api.getFindings).mockResolvedValue({ items: [], total: 0 });
    vi.mocked(api.getFindingsSummary).mockResolvedValue({ critical: 0, high: 0, medium: 0, low: 0, info: 0, total: 0 });
    vi.mocked(api.getActivities).mockResolvedValue([]);

    render(<DashboardPage />);

    expect(screen.getByText('Command Center')).toBeInTheDocument();
    expect(screen.getByText('CONTROL ROOM')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('No Repositories Connected')).toBeInTheDocument();
      expect(screen.getByText('No Services Discovered')).toBeInTheDocument();
      expect(screen.getByText('Zero Findings Recorded')).toBeInTheDocument();
      expect(screen.getByText('No Recent Activity Logged')).toBeInTheDocument();
    });
  });

  it('renders real telemetry and populated entities when data is available', async () => {
    vi.mocked(api.getSystemStatus).mockResolvedValue({
      status: 'healthy',
      database_connected: true,
      database_dialect: 'mysql',
      database_latency_ms: 0.8,
      api_version: '0.1.0',
      uptime_seconds: 120.0,
      timestamp: new Date().toISOString(),
      active_connections: 1,
    });
    vi.mocked(api.getSystemSummary).mockResolvedValue({
      repositories_count: 1,
      services_count: 1,
      findings_count: 1,
      findings_by_severity: { critical: 1, high: 0, medium: 0, low: 0, info: 0, total: 1 },
      services_healthy_count: 1,
      services_degraded_count: 0,
      system_status: 'degraded',
      timestamp: new Date().toISOString(),
    });
    vi.mocked(api.getRepositories).mockResolvedValue({
      items: [
        {
          id: 'repo-1',
          name: 'Mirror-X',
          url: 'https://github.com/Taher-sys/Mirror-X',
          default_branch: 'main',
          language: 'TypeScript',
          status: 'active',
          project_id: 'proj-1',
          services_count: 1,
          findings_count: 1,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
      total: 1,
    });
    vi.mocked(api.getServices).mockResolvedValue({
      items: [
        {
          id: 'svc-1',
          name: 'gateway-api',
          service_type: 'api',
          status: 'healthy',
          runtime: 'Node 20',
          version: 'v1.0.0',
          repository_id: 'repo-1',
          repository_name: 'Mirror-X',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
      total: 1,
    });
    vi.mocked(api.getFindings).mockResolvedValue({
      items: [
        {
          id: 'f-1',
          title: 'API Drift: schema mismatch',
          finding_type: 'schema_mismatch',
          severity: 'critical',
          confidence: 0.95,
          description: 'Parameter mismatch between spec and handler',
          status: 'open',
          repository_id: 'repo-1',
          service_id: 'svc-1',
          service_name: 'gateway-api',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
      total: 1,
    });
    vi.mocked(api.getFindingsSummary).mockResolvedValue({
      critical: 1,
      high: 0,
      medium: 0,
      low: 0,
      info: 0,
      total: 1,
    });
    vi.mocked(api.getActivities).mockResolvedValue([
      {
        id: 'act-1',
        actor: 'user',
        action: 'repository_connected',
        entity_type: 'repository',
        entity_name: 'Mirror-X',
        details: 'Connected Mirror-X repository',
        created_at: new Date().toISOString(),
      },
    ]);

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getAllByText('Mirror-X').length).toBeGreaterThan(0);
      expect(screen.getAllByText('gateway-api').length).toBeGreaterThan(0);
      expect(screen.getByText('API Drift: schema mismatch')).toBeInTheDocument();
      expect(screen.getByText('repository connected')).toBeInTheDocument();
    });

  });
});
