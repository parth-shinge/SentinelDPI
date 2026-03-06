import axios from "axios";
import type { Metrics } from "../types/metrics";
import type { AlertsSnapshot } from "../types/alerts";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  timeout: 5000,
});

/** Fetch current metrics snapshot via REST (fallback). */
export async function getMetrics(): Promise<Metrics> {
  const { data } = await api.get<Metrics>("/metrics");
  return data;
}

/** Fetch alert history via REST (fallback). */
export async function getAlerts(): Promise<AlertsSnapshot> {
  const { data } = await api.get<AlertsSnapshot>("/alerts");
  return data;
}
