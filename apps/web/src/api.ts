import type { CreateIncidentInput, Incident, IncidentSeverity } from '@emanaguard/shared';

export async function fetchIncidents(): Promise<Incident[]> {
  const res = await fetch('/api/incidents');
  if (!res.ok) throw new Error('Failed to load incidents');
  const data = (await res.json()) as { incidents: Incident[] };
  return data.incidents;
}

export async function createIncident(input: CreateIncidentInput): Promise<Incident> {
  const res = await fetch('/api/incidents', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as { error?: string };
    throw new Error(body.error ?? 'Failed to create incident');
  }
  const data = (await res.json()) as { incident: Incident };
  return data.incident;
}

export async function resolveIncident(id: string): Promise<Incident> {
  const res = await fetch(`/api/incidents/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'resolved' }),
  });
  if (!res.ok) throw new Error('Failed to resolve incident');
  const data = (await res.json()) as { incident: Incident };
  return data.incident;
}

export const SEVERITY_OPTIONS: IncidentSeverity[] = ['low', 'medium', 'high', 'critical'];
