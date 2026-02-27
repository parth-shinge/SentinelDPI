# SentinelDPI

SentinelDPI is a modular, multi-threaded Deep Packet Inspection (DPI) engine with real-time telemetry streaming, pluggable intrusion detection, structured alerting, and a production-grade React dashboard.

The system is engineered using clean architecture principles, strict separation of concerns, dependency injection, and event-driven communication to ensure scalability, maintainability, and production readiness.

---

## Key Capabilities

### Multi-Threaded Packet Processing
- Scapy-based packet capture (Windows + Npcap)
- Dedicated capture and processing threads
- Thread-safe queue pipeline
- Graceful lifecycle management
- No global state

### Structured Parsing Layer
- Stateless `PacketParser`
- Typed `PacketFeatures` contract
- Defensive layer handling (never crashes on missing layers)
- Clear separation from detection logic

### Pluggable Detection Framework
- Abstract `BaseDetector` interface
- `DetectionManager` orchestration
- Sliding-window Port Scan detection
- Sustained High Traffic (PPS) detection
- Zero coupling between detectors

### Metrics Engine
- Total packet tracking
- Per-protocol distribution
- Top source/destination tracking
- Rolling packets-per-second (PPS)
- Bounded in-memory design

### Alert Management
- UUID-enriched alerts
- Severity mapping
- Cooldown-based deduplication
- Bounded alert history
- Observer-style listener pattern

### Real-Time Streaming API
- REST endpoints:
  - `/health`
  - `/metrics`
  - `/alerts`
- WebSocket endpoint:
  - `/ws`
- Event-driven push (no polling)
- Exponential backoff reconnect logic (frontend)

### Production Logging
- Structured JSON logs
- Aggregation-ready format
- No third-party logging frameworks

### Frontend Dashboard
- React + TypeScript
- Tailwind CSS design system
- Animated stat transitions
- Real-time WebSocket updates
- Alert toast notifications
- Threat feed sidebar
- Auto-scrolling alert table
- Connection status indicator

### Containerized Deployment
- Dockerized backend (Python 3.11 slim)
- Dockerized frontend (multi-stage build + Nginx)
- docker-compose full stack orchestration

---

## Architecture Overview

```
CaptureEngine
    ↓
PacketQueue
    ↓
PacketProcessor
    ↓
PacketParser
    ↓
MetricsService
    ↓
DetectionManager
    ↓
AlertManager
    ↓
FastAPI (REST + WebSocket)
    ↓
React Dashboard (Real-Time Streaming)
```

---

## Local Development

### Backend

```bash
python -m sentinel_dpi.main
```

Backend runs at:
http://127.0.0.1:8000

---

### Frontend

```bash
cd dashboard
npm install
npm run dev
```

Frontend runs at:
http://localhost:5173

---

## Docker Deployment

```bash
docker compose up --build
```

Frontend:
http://localhost

Backend:
http://localhost:8000

---

## Testing

```bash
python -m pytest tests/ -v
```

All tests must pass before deployment.

---

## Engineering Principles

- No global state
- Strict separation of concerns
- Dependency injection across layers
- Bounded memory usage
- Event-driven architecture
- Regression-safe test coverage
- Structured production logging
- Container-ready deployment

---

## About

SentinelDPI was built as a systems-focused backend architecture project exploring:

- Concurrent system design
- Sliding-window anomaly detection
- Real-time telemetry streaming
- Alert deduplication strategies
- Plugin-based detection architecture
- Full-stack integration via WebSockets
- Production deployment patterns