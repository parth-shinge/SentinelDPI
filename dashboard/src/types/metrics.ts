/** Shape returned by GET /metrics */
export interface MetricsSnapshot {
  total_packets: number;
  packets_per_protocol: Record<string, number>;
  packets_per_source_ip: Record<string, number>;
  packets_per_destination_ip: Record<string, number>;
  packets_per_second: number;
}
