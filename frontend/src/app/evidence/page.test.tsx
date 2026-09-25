import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import EvidencePage from './page';

describe('EvidencePage', () => {
  it('renders the Evidence Ledger console', () => {
    render(<EvidencePage />);

    expect(screen.getByText('Evidence Ledger')).toBeInTheDocument();
    expect(screen.getByText(/VERIFIABLE PROVENANCE/)).toBeInTheDocument();
    expect(screen.getByText(/SHA-256 PROVENANCE ACTIVE/)).toBeInTheDocument();
  });
});
