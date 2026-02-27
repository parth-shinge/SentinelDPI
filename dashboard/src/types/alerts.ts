/** A single enriched alert as stored by AlertManager. */
export interface Alert {
  id: string;
  type: string;
  source_ip: string | null;
  severity: string;
  timestamp: number;
}

/** Shape returned by GET /alerts */
export interface AlertsSnapshot {
  total_alerts: number;
  recent_alerts: Alert[];
  alerts_by_type: Record<string, number>;
}
