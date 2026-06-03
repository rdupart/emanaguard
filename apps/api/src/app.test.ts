import { afterEach, describe, expect, it } from 'vitest';
import request from 'supertest';
import { createApp } from './app.js';
import { resetStore } from './store.js';

describe('API', () => {
  afterEach(() => {
    resetStore();
  });

  it('returns health', async () => {
    const res = await request(createApp()).get('/api/health');
    expect(res.status).toBe(200);
    expect(res.body.ok).toBe(true);
  });

  it('creates and lists incidents', async () => {
    const app = createApp();
    const created = await request(app)
      .post('/api/incidents')
      .send({ title: 'Flood warning', severity: 'critical' });
    expect(created.status).toBe(201);

    const list = await request(app).get('/api/incidents');
    expect(list.body.incidents).toHaveLength(1);
    expect(list.body.incidents[0].title).toBe('Flood warning');
  });

  it('resolves an incident', async () => {
    const app = createApp();
    const created = await request(app)
      .post('/api/incidents')
      .send({ title: 'Drill complete', severity: 'low' });
    const id = created.body.incident.id;

    const resolved = await request(app)
      .patch(`/api/incidents/${id}`)
      .send({ status: 'resolved' });
    expect(resolved.body.incident.status).toBe('resolved');
  });
});
