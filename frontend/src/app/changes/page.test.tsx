import { render, act } from '@testing-library/react';
import { screen, waitFor, fireEvent } from '@testing-library/dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ChangesPage from './page';
import * as api from '@/lib/api';

vi.mock('@/lib/api', () => ({
  analyzeChangeImpact: vi.fn(),
  getChangeRecords: vi.fn(),
}));

describe('ChangesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the Change Twin dual-pane view with awaiting simulation state', () => {
    render(<ChangesPage />);

    expect(screen.getByText('Change Twin')).toBeInTheDocument();
    expect(screen.getByText('BLAST RADIUS CASCADE')).toBeInTheDocument();
    expect(screen.getByText('Proposed Git Change')).toBeInTheDocument();
    expect(screen.getByText('Awaiting Impact Simulation')).toBeInTheDocument();
  });

  it('triggers blast radius simulation and renders impacted topology entities', async () => {
    const mockImpact: api.ChangeImpactAnalysisResult = {
      record_id: 'rec-1',
      title: 'PR #104: Optimize order processing pipeline',
      branch: 'feature/fast-orders',
      author: 'dev@test.com',
      direct_impact_count: 1,
      indirect_impact_count: 1,
      total_impacted_nodes: 2,
      risk_score: 45.0,
      risk_level: 'high',
      affected_categories: { service: 2 },
      breaking_changes: [
        {
          title: 'High Blast Radius on orders-service',
          severity: 'high',
          source_node: 'orders-service',
          impacted_nodes: ['checkout-service'],
          description: 'Modifying orders-service propagates to checkout-service',
        },
      ],
      direct_nodes: [
        {
          node_id: 'n-1',
          name: 'orders-service',
          node_type: 'service',
          path: 'services/orders/main.py',
          reason: "File 'services/orders/main.py' modified in change payload",
        },
      ],
      indirect_nodes: [
        {
          node_id: 'n-2',
          name: 'checkout-service',
          node_type: 'service',
          path: 'services/checkout/main.py',
          depth: 1,
          propagation_path: ['orders-service', '(calls)', 'checkout-service'],
          reason: 'Upstream consumer: checkout-service calls orders-service',
        },
      ],
      modified_files: [
        {
          file_path: 'services/orders/main.py',
          change_type: 'modified',
          additions: 2,
          deletions: 1,
        },
      ],
    };

    vi.mocked(api.analyzeChangeImpact).mockResolvedValue(mockImpact);

    render(<ChangesPage />);

    // Click Simulate Blast Radius button
    const simButton = screen.getByRole('button', { name: /simulate blast radius/i });
    fireEvent.click(simButton);

    await waitFor(() => {
      expect(api.analyzeChangeImpact).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getAllByText('orders-service')[0]).toBeInTheDocument();
    });

    expect(screen.getAllByText('checkout-service')[0]).toBeInTheDocument();
    expect(screen.getByText(/Breaking Changes Detected/i)).toBeInTheDocument();
    expect(screen.getByText('HIGH')).toBeInTheDocument();
  });
});
