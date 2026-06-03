import type { Incident, IncidentSeverity } from '@emanaguard/shared';
import { FormEvent, useCallback, useEffect, useState } from 'react';
import { SEVERITY_OPTIONS, createIncident, fetchIncidents, resolveIncident } from './api.js';

export function App() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [title, setTitle] = useState('');
  const [severity, setSeverity] = useState<IncidentSeverity>('medium');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      setIncidents(await fetchIncidents());
    } catch {
      setError('Could not reach the API. Is the API running on port 3001?');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await createIncident({ title, severity });
      setTitle('');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Create failed');
    } finally {
      setSubmitting(false);
    }
  }

  async function onResolve(id: string) {
    setError(null);
    try {
      await resolveIncident(id);
      await load();
    } catch {
      setError('Failed to resolve incident');
    }
  }

  return (
    <main>
      <h1>emanaguard</h1>
      <p className="subtitle">Emergency incident tracker for local development</p>

      <section className="card" aria-labelledby="new-incident">
        <h2 id="new-incident">Report incident</h2>
        <form onSubmit={onSubmit}>
          <label>
            Title
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Shelter capacity alert"
              required
            />
          </label>
          <label>
            Severity
            <select value={severity} onChange={(e) => setSeverity(e.target.value as IncidentSeverity)}>
              {SEVERITY_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <button type="submit" disabled={submitting}>
            {submitting ? 'Saving…' : 'Create incident'}
          </button>
        </form>
      </section>

      <section className="card" aria-labelledby="incidents">
        <h2 id="incidents">Active board</h2>
        {error && <p className="error">{error}</p>}
        {loading && <p className="empty">Loading…</p>}
        {!loading && incidents.length === 0 && (
          <p className="empty">No incidents yet. Create one above.</p>
        )}
        <ul className="incident-list">
          {incidents.map((incident) => (
            <li key={incident.id} className="incident-item">
              <div>
                <strong>{incident.title}</strong>
                <div>
                  <span className={`badge ${incident.severity}`}>{incident.severity}</span>{' '}
                  <span className={`badge ${incident.status === 'resolved' ? 'resolved' : ''}`}>
                    {incident.status}
                  </span>
                </div>
              </div>
              {incident.status === 'open' && (
                <button type="button" className="secondary" onClick={() => void onResolve(incident.id)}>
                  Resolve
                </button>
              )}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
