import axios from "axios";
import type { MetricsSnapshot } from "../types/metrics";
import type { AlertsSnapshot } from "../types/alerts";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  timeout: 5000,
});

export async function getMetrics(): Promise<MetricsSnapshot> {
  const { data } = await api.get<MetricsSnapshot>("/metrics");
  return data;
}

export async function getAlerts(): Promise<AlertsSnapshot> {
  const { data } = await api.get<AlertsSnapshot>("/alerts");
  return data;
}
