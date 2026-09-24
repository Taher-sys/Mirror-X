import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ContextPage from './page';
import * as api from '@/lib/api';

vi.mock('@/lib/api', () => ({
  analyzeContext: vi.fn(),
  getContextFindings: vi.fn(),
  getContextFindingDetail: vi.fn(),
  updateFindingStatus: vi.fn(),
  getContextStatistics: vi.fn(),
}));

describe('ContextPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the context engine page with honest empty state', async () => {
    vi.mocked(api.getContextFindings).mockResolvedValue([]);
    vi.mocked(api.getContextStatistics).mockResolvedValue({
      total_findings: 0,
      findings_by_type: {},
      findings_by_severity: { critical: 0, high: 0, medium: 0, low: 0 },
      findings_by_status: { open: 0, resolved: 0, dismissed: 0 },
      resolution_rate: 0.0,
    });

    render(<ContextPage />);

    expect(screen.getByText('Context Engine')).toBeInTheDocument();
    expect(screen.getByText('DRIFT MATRIX')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/No Discrepancies Found/i)).toBeInTheDocument();
    });
  });

  it('renders discrepancy cards and opens evidence inspection modal', async () => {
    const mockFinding: api.Finding = {
      id: 'f-123',
      title: 'Data Type Mismatch on orders.total',
      finding_type: 'schema_mismatch',
      severity: 'critical',
      confidence: 0.98,
      description: 'Model Order defines total as str, but schema defines DECIMAL',
      evidence_payload: {
        file_path: 'models/order.py',
        line_number: 14,
        expected: 'DECIMAL(10,2)',
        actual: 'str',
      },
      status: 'open',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    vi.mocked(api.getContextFindings).mockResolvedValue([mockFinding]);
    vi.mocked(api.getContextStatistics).mockResolvedValue({
      total_findings: 1,
      findings_by_type: { schema_mismatch: 1 },
      findings_by_severity: { critical: 1, high: 0, medium: 0, low: 0 },
      findings_by_status: { open: 1, resolved: 0, dismissed: 0 },
      resolution_rate: 0.0,
    });
    vi.mocked(api.getContextFindingDetail).mockResolvedValue({
      finding: mockFinding,
      related_nodes: [
        {
          id: 'n-1',
          name: 'orders',
          node_type: 'table',
          path: 'schema.sql',
        },
      ],
    });

    render(<ContextPage />);

    await waitFor(() => {
      expect(screen.getByText('Data Type Mismatch on orders.total')).toBeInTheDocument();
      expect(screen.getByText(/98% EVIDENCE CONFIDENCE/i)).toBeInTheDocument();
    });

    // Click on inspect
    fireEvent.click(screen.getByText('Inspect'));

    await waitFor(() => {
      expect(screen.getByText(/Analytical Conclusion/i)).toBeInTheDocument();
      expect(screen.getByText(/Expected Architectural State/i)).toBeInTheDocument();
      expect(screen.getByText(/Observed Reality Drift/i)).toBeInTheDocument();
    });
  });
});
