# XtremIO Storage Monitoring for Zabbix

Python-based monitoring solution for Dell EMC XtremIO Storage arrays using the XtremIO REST API and Zabbix Sender.

This project automatically discovers storage objects and sends performance, capacity, health, and alert metrics to Zabbix.

---

## Features

- Automatic Low-Level Discovery (LLD)
- Multi-threaded data collection
- Performance monitoring
- Capacity monitoring
- Hardware health monitoring
- XtremIO Alert discovery
- Numeric and string metric support
- Direct integration with Zabbix Sender
- REST API communication with XtremIO

---

## Components

### XIO_monitoring.py

Collects monitoring metrics including:

- Clusters
- Volumes
- SSDs
- Storage Controllers
- DAE Controllers
- Target Groups
- Bricks
- Infiniband Switches
- LUN Maps

Supports both:

- Discovery Mode
- Value Collection Mode

---

### XIO_alert.py

Collects active XtremIO alerts and publishes them to Zabbix.

Ignored alert states:

- clear
- acknowledged

Collected fields include:

- Severity
- Description
- Object Name
- Alert Type
- Alert State
- System Name

---

## Architecture

```
XtremIO Storage
        │
 REST API (HTTPS)
        │
Python Scripts
        │
Zabbix Sender
        │
Zabbix Server
        │
Dashboards & Triggers
```

---

## Requirements

- Python 3.9+
- requests
- urllib3
- py-zabbix

Install:

```bash
pip install requests urllib3 py-zabbix
```

---

## Usage

### Monitoring

```bash
python XIO_monitoring.py value <XIO_IP> <ZABBIX_HOSTNAME>
```

Discovery

```bash
python XIO_monitoring.py discovery <XIO_IP> <ZABBIX_HOSTNAME>
```

Alerts

```bash
python XIO_alert.py alert <XIO_IP> <ZABBIX_HOSTNAME>
```

---

## Monitored Metrics

Examples include:

- IOPS
- Bandwidth
- Latency
- SSD Health
- Capacity Utilization
- Data Reduction Ratio
- Controller Health
- Firmware Status
- Temperature
- Port Status
- Storage Alerts

---

## Security

For public repositories, credentials should be supplied through environment variables or a secure configuration file rather than hardcoded values.

---

## Future Improvements

- Environment variable support
- YAML configuration
- Logging module
- Retry mechanism
- Docker support
- Unit tests
- GitHub Actions CI

---

## License

MIT License

---

## Author

Behzad Kianbakht

Senior Site Reliability Engineer | Automation Engineer | Python Developer | Monitoring & Observability