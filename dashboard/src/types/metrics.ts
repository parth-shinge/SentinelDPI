import type { Alert } from "./alerts";

/** Core traffic metrics from the backend. */
export interface Metrics {
  total_packets: number;
  packets_per_protocol: Record<string, number>;
  packets_per_source_ip: Record<string, number>;
  packets_per_destination_ip: Record<string, number>;
  packets_per_second: number;
}

/** System health status from the backend. */
export interface SystemStatusData {
  capture_engine: string;
  packet_processor: string;
  websocket: string;
  detectors_loaded: number;
}

/** Per-minute alert count for the activity timeline. */
export interface AlertActivityEntry {
  time: string;
  count: number;
}

/** Traffic feed entry. */
export interface TrafficFeedEntry {
  src_ip: string;
  dst_ip: string;
  protocol: string;
  timestamp: number;
}

/** Top talker entry. */
export interface TopTalkerEntry {
  ip: string;
  packets: number;
}

/** Structured telemetry snapshot from the WebSocket metrics tick. */
export interface TelemetrySnapshot {
  metrics: Metrics;
  top_talkers: TopTalkerEntry[];
  traffic_feed: TrafficFeedEntry[];
  threat_level: "LOW" | "MEDIUM" | "HIGH";
  system_status: SystemStatusData;
  alert_activity: AlertActivityEntry[];
  alerts: Alert[];
}
