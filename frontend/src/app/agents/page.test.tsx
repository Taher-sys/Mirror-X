import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import AgentsPage from './page';

describe('AgentsPage', () => {
  it('renders the agents page with empty state', () => {
    render(<AgentsPage />);

    expect(screen.getByText('Agent Behavior Lab')).toBeInTheDocument();
    expect(screen.getByText(/No agent telemetry/)).toBeInTheDocument();
  });
});
