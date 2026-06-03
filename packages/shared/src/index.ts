export type IncidentSeverity = 'low' | 'medium' | 'high' | 'critical';

export type IncidentStatus = 'open' | 'resolved';

export interface Incident {
  id: string;
  title: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  createdAt: string;
  updatedAt: string;
}

export interface CreateIncidentInput {
  title: string;
  severity: IncidentSeverity;
}

export interface UpdateIncidentInput {
  status?: IncidentStatus;
}
