import { describe, expect, it } from 'vitest';
import type { Incident } from './index.js';

describe('Incident types', () => {
  it('accepts a valid incident shape', () => {
    const incident: Incident = {
      id: '1',
      title: 'Power outage at site A',
      severity: 'high',
      status: 'open',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    expect(incident.status).toBe('open');
  });
});
