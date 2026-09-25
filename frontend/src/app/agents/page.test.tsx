import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import AgentsPage from './page';

describe('AgentsPage', () => {
  it('renders the Agent Behavior Lab console', () => {
    render(<AgentsPage />);

    expect(screen.getByText('Agent Behavior Lab')).toBeInTheDocument();
    expect(screen.getByText(/SANDBOX BEHAVIOR MATRIX/)).toBeInTheDocument();
    expect(screen.getByText(/Run Agent Goal/)).toBeInTheDocument();
  });
});
