import type { CreateIncidentInput, Incident, UpdateIncidentInput } from '@emanaguard/shared';
import { randomUUID } from 'node:crypto';

const incidents = new Map<string, Incident>();

export function listIncidents(): Incident[] {
  return [...incidents.values()].sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
  );
}

export function createIncident(input: CreateIncidentInput): Incident {
  const now = new Date().toISOString();
  const incident: Incident = {
    id: randomUUID(),
    title: input.title.trim(),
    severity: input.severity,
    status: 'open',
    createdAt: now,
    updatedAt: now,
  };
  incidents.set(incident.id, incident);
  return incident;
}

export function updateIncident(id: string, input: UpdateIncidentInput): Incident | undefined {
  const existing = incidents.get(id);
  if (!existing) return undefined;

  const updated: Incident = {
    ...existing,
    ...input,
    updatedAt: new Date().toISOString(),
  };
  incidents.set(id, updated);
  return updated;
}

export function resetStore(): void {
  incidents.clear();
}
