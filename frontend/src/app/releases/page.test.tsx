import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ReleasesPage from './page';

describe('ReleasesPage', () => {
  it('renders the Release Passport console', () => {
    render(<ReleasesPage />);

    expect(screen.getByText('Release Passport')).toBeInTheDocument();
    expect(screen.getByText(/VERIFIABLE CERTIFICATION/)).toBeInTheDocument();
    expect(screen.getAllByText(/Issue \/ Re-Evaluate Passport/)[0]).toBeInTheDocument();
  });
});
