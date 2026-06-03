import type { CreateIncidentInput, IncidentSeverity } from '@emanaguard/shared';
import cors from 'cors';
import express from 'express';
import { createIncident, listIncidents, updateIncident } from './store.js';

const SEVERITIES: IncidentSeverity[] = ['low', 'medium', 'high', 'critical'];

export function createApp() {
  const app = express();
  app.use(cors());
  app.use(express.json());

  app.get('/api/health', (_req, res) => {
    res.json({ ok: true, service: 'emanaguard-api' });
  });

  app.get('/api/incidents', (_req, res) => {
    res.json({ incidents: listIncidents() });
  });

  app.post('/api/incidents', (req, res) => {
    const body = req.body as Partial<CreateIncidentInput>;
    const title = typeof body.title === 'string' ? body.title.trim() : '';
    const severity = body.severity;

    if (!title) {
      res.status(400).json({ error: 'title is required' });
      return;
    }
    if (!severity || !SEVERITIES.includes(severity)) {
      res.status(400).json({ error: 'severity must be low, medium, high, or critical' });
      return;
    }

    const incident = createIncident({ title, severity });
    res.status(201).json({ incident });
  });

  app.patch('/api/incidents/:id', (req, res) => {
    const { status } = req.body as { status?: string };
    if (status !== undefined && status !== 'open' && status !== 'resolved') {
      res.status(400).json({ error: 'status must be open or resolved' });
      return;
    }

    const incident = updateIncident(req.params.id, status ? { status } : {});
    if (!incident) {
      res.status(404).json({ error: 'incident not found' });
      return;
    }
    res.json({ incident });
  });

  return app;
}
