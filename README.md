# IoT IDS (Intrusion Detection System)

A comprehensive IoT Intrusion Detection System using Docker containers for MQTT monitoring, network analysis, and log aggregation.

## Repository

This project uses Git for version control. To get started:

```bash
# Clone the repository
git clone https://github.com/Rakesh2109/iot-mqtt-server-pi.git
cd Pi_Server

# Or if working with an existing local repository
git status
```

**GitHub Repository**: [https://github.com/Rakesh2109/iot-mqtt-server-pi](https://github.com/Rakesh2109/iot-mqtt-server-pi)

## Architecture

- **Mosquitto**: MQTT broker for IoT device communication (high-speed message ingestion)
- **Suricata**: Network IDS/IPS for traffic analysis and pcap capture
- **Zeek**: Network analysis framework for deep packet inspection
- **InfluxDB**: Time-series database for metrics and data storage
- **Loki**: Log aggregation system
- **Grafana**: Web dashboard for real-time monitoring and visualization
- **Flask API**: Data processing, MQTT to InfluxDB/Loki forwarding
- **Traffic Monitor**: Web-based traffic monitoring dashboard

## Prerequisites

- Docker and Docker Compose installed
- Network access for monitoring (Suricata uses host networking)

## Quick Start

1. **Start all services:**
   ```bash
   docker compose up -d
   ```

2. **Check service status:**
   ```bash
   docker compose ps
   ```

3. **View logs:**
   ```bash
   docker compose logs -f
   ```

## Service Access

- **Traffic Monitoring Dashboard**: http://localhost:8080
  - Real-time traffic visualization
  - Message statistics and topic distribution
  - Auto-refreshes every 5 seconds

- **Grafana Dashboard**: http://localhost:3000
  - Username: `admin`
  - Password: `admin`
  - Advanced analytics and dashboards
  - Connected to InfluxDB and Loki
  
- **InfluxDB**: http://localhost:8086
  - Username: `admin`
  - Password: `admin123`
  - Organization: `iot-ids`
  - Bucket: `iot-data`
  
- **Flask API**: http://localhost:5000
  - Health check: http://localhost:5000/health
  - Stats: http://localhost:5000/api/stats
  - Metrics: http://localhost:5000/api/metrics
  - Traffic dashboard: http://localhost:5000/traffic

- **Mosquitto MQTT**: 
  - Port 1883 (MQTT)
  - Port 9001 (WebSocket)

- **Loki**: http://localhost:3100

## Configuration

### Mosquitto
Edit `mosquitto/config/mosquitto.conf` to customize MQTT broker settings.

### Suricata
Edit `suricata/config/suricata.yaml` to configure IDS rules and detection.

### Grafana
- Datasources: `grafana/provisioning/datasources/`
- Dashboards: `grafana/dashboards/`

### InfluxDB
- Default credentials: admin/admin123
- Change token in `docker-compose.yml` for production
- Data retention and policies can be configured via InfluxDB UI

### Zeek
- Edit `zeek/config/node.cfg` to configure network interface
- Update `INTERFACE` environment variable in `docker-compose.yml` if needed
- Logs are stored in `zeek/logs/`

### Flask API
Edit `flask/app.py` to customize data processing logic.

## Stopping Services

```bash
docker compose down
```

To remove volumes:
```bash
docker compose down -v
```

## Data Storage

- **InfluxDB**: Time-series metrics and MQTT message data
- **Loki**: Log aggregation and search
- **PCAP Files**: `suricata/pcap/` - Network packet captures (1GB per file, max 2000 files)
- **Zeek Logs**: `zeek/logs/` - Network analysis logs

## Logs Location

- Mosquitto: `mosquitto/log/`
- Suricata: `suricata/logs/` and `suricata/pcap/`
- Zeek: `zeek/logs/`
- Flask: Check container logs with `docker compose logs flask`

## Development

### Repository Structure

```
Pi_Server/
├── docker-compose.yml          # Main orchestration file
├── flask/                      # Flask API service
├── grafana/                    # Grafana configuration and dashboards
├── loki/                       # Loki log aggregation config
├── mosquitto/                  # MQTT broker configuration
├── suricata/                   # Network IDS configuration
├── traffic-monitor/            # Web traffic monitoring dashboard
└── zeek/                       # Network analysis framework config
```

### Contributing

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Commit: `git commit -m "Add your feature"`
4. Push: `git push origin feature/your-feature-name`

## Security Notes

- Change default Grafana credentials in production
- Configure Mosquitto authentication for production use
- Review Suricata rules for your network environment
- Update Flask API security settings before deployment

