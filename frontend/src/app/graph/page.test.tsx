import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import GraphPage from './page';
import * as api from '@/lib/api';

vi.mock('@/lib/api', () => ({
  getGraph: vi.fn(),
  getGraphStatistics: vi.fn(),
  getNodeDetails: vi.fn(),
}));

describe('GraphPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the graph page with honest empty state', async () => {
    vi.mocked(api.getGraph).mockResolvedValue({
      nodes: [],
      edges: [],
      total_nodes: 0,
      total_edges: 0,
    });
    vi.mocked(api.getGraphStatistics).mockResolvedValue({
      total_nodes: 0,
      total_edges: 0,
      nodes_by_type: {},
      edges_by_relationship: {},
      graph_density: 0.0,
    });

    render(<GraphPage />);

    expect(screen.getByText('Reality Graph')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getAllByText(/No nodes to display/)[0]).toBeInTheDocument();
    });
  });

  it('renders the reality graph canvas and statistics when nodes exist', async () => {
    vi.mocked(api.getGraph).mockResolvedValue({
      nodes: [
        {
          id: 'n1',
          node_type: 'service',
          name: 'payment-service',
          path: '/services/payment',
          properties: { version: '1.0.0' },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: 'n2',
          node_type: 'database',
          name: 'payment-db',
          properties: { dialect: 'postgres' },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
      edges: [
        {
          id: 'e1',
          source_node_id: 'n1',
          target_node_id: 'n2',
          relationship_type: 'depends_on',
          properties: {},
          created_at: new Date().toISOString(),
        },
      ],
      total_nodes: 2,
      total_edges: 1,
    });
    vi.mocked(api.getGraphStatistics).mockResolvedValue({
      total_nodes: 2,
      total_edges: 1,
      nodes_by_type: { service: 1, database: 1 },
      edges_by_relationship: { depends_on: 1 },
      graph_density: 0.5,
    });

    render(<GraphPage />);

    expect(screen.getByText('Reality Graph')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('payment-service')).toBeInTheDocument();
      expect(screen.getByText('payment-db')).toBeInTheDocument();
      expect(screen.getByText('NODES:')).toBeInTheDocument();
    });
  });
});
