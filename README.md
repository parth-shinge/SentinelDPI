# SentinelDPI

**SentinelDPI** is a modular, multi-threaded Deep Packet Inspection (DPI) engine with pluggable intrusion detection, real-time traffic metrics, alert deduplication, and a FastAPI service layer.

It is designed using clean architecture principles, strict separation of concerns, and dependency injection to ensure extensibility, testability, and production readiness.

---

## Key Features

### Multi-Threaded Capture Pipeline
- Continuous packet capture (Windows + Npcap)
- Thread-safe queue between capture and processing layers
- Graceful start/stop lifecycle management

### Clean Parsing Layer
- Stateless `PacketParser`
- Normalized packet feature extraction
- Protocol-aware handling (TCP, UDP, ICMP, Other)
- Defensive layer handling (never crashes on missing layers)

### Pluggable Detection Framework
- Abstract `BaseDetector`
- `DetectionManager` orchestrator
- Sliding-window Port Scan Detector implementation
- Cooldown-based alert suppression

### Real-Time Metrics Engine
- Total packet count
- Packets per protocol
- Top source/destination IP tracking
- Rolling packets-per-second (PPS)
- Bounded memory usage

### Alert Management
- UUID-enriched alert objects
- Severity mapping
- Cooldown-based deduplication
- Bounded alert history (configurable)

### HTTP API Layer (FastAPI)
- `GET /health`
- `GET /metrics`
- `GET /alerts`
- Read-only snapshot exposure
- No coupling with packet or detection internals

### Fully Tested
- 53 unit tests
- Regression-safe architecture
- Detection, metrics, alerts, and API covered

---

## Architecture Overview

CaptureEngine → PacketQueue → PacketProcessor → PacketParser → MetricsService → DetectionManager → AlertManager → FastAPI API Layer

### Architectural Principles

- No global state
- Strict layer separation
- Dependency injection throughout
- No business logic in capture layer
- Bounded memory usage
- Extensible detector plugin model
- Read-only API exposure

---

## API Endpoints

| Method | Endpoint   | Description |
|--------|------------|------------|
| GET    | /health    | Service health check |
| GET    | /metrics   | Real-time traffic statistics |
| GET    | /alerts    | Recent detection alerts |

### Example Response: `/health`

json
{
  "status": "ok"
}

### Example Response: `/alerts`

json
{
  "total_alerts": 2,
  "recent_alerts": [
    {
      "id": "uuid",
      "type": "PORT_SCAN",
      "source_ip": "192.168.1.4",
      "severity": "HIGH",
      "timestamp": 1771957120.27
    }
  ],
  "alerts_by_type": {
    "PORT_SCAN": 2
  }
}

---

## Installation

### Requirements

- Python 3.11+
- Windows
- Npcap (Admin-restricted mode recommended)

### Install Dependencies

pip install -r requirements.txt

---

## Running SentinelDPI

python -m sentinel_dpi.main

API available at:

http://127.0.0.1:8000

Press `Ctrl+C` for graceful shutdown.

---

## Running Tests

bash
python -m pytest tests/ -v

All tests should pass.

---

## Configuration

All tunables are centralized in:

sentinel_dpi/config/settings.py

Includes:

- Capture settings
- Detection thresholds
- Alert cooldown and history
- API enable/disable toggle
- Host and port configuration

---

## Future Improvements

- Web dashboard (real-time visualization)
- Persistent alert storage
- Additional anomaly detectors
- ML-based detection modules
- Distributed sensor mode
- Role-based access control

---

## About the Project

SentinelDPI was built as a systems-focused backend project to explore:

- Concurrent architecture design
- Real-time network traffic processing
- Sliding-window detection algorithms
- Alert deduplication strategies
- Clean dependency injection patterns
- Service-layer exposure via FastAPI
- Writing maintainable, testable code
