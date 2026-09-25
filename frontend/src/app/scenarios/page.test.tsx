import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ScenariosPage from './page';

describe('ScenariosPage', () => {
  it('renders the Synthetic Scenario Engine console', () => {
    render(<ScenariosPage />);

    expect(screen.getByText('Synthetic Scenario Engine')).toBeInTheDocument();
    expect(screen.getByText(/REPRODUCIBLE TEST TWIN/)).toBeInTheDocument();
    expect(screen.getByText(/Generate Suite/)).toBeInTheDocument();
  });
});
