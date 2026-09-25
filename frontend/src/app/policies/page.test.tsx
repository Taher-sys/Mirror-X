import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import PoliciesPage from './page';

describe('PoliciesPage', () => {
  it('renders the Trust Layer Policy & Permissions console', () => {
    render(<PoliciesPage />);

    expect(screen.getByText('Trust Layer: Policy & Permissions')).toBeInTheDocument();
    expect(screen.getByText(/PRODUCTION ACTIONS PROHIBITED/)).toBeInTheDocument();
    expect(screen.getByText(/Evaluate Policy Gate/)).toBeInTheDocument();
  });
});
