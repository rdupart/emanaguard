import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { App } from './App.js';

vi.mock('./api.js', () => ({
  SEVERITY_OPTIONS: ['low', 'medium', 'high', 'critical'],
  fetchIncidents: vi.fn().mockResolvedValue([]),
  createIncident: vi.fn(),
  resolveIncident: vi.fn(),
}));

describe('App', () => {
  it('renders the product title', async () => {
    render(<App />);
    expect(screen.getByRole('heading', { level: 1, name: 'emanaguard' })).toBeInTheDocument();
    expect(await screen.findByText(/No incidents yet/)).toBeInTheDocument();
  });
});
