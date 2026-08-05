# Monitoring & Telemetry

TestPilot AI includes real-time telemetry and task queue monitoring to ensure system health and LLM cost visibility.

---

## 📊 System Metrics & Monitoring

### Monitored Indicators:
- **Celery Task Queue Latency**: Real-time worker task queue processing times via Redis.
- **LLM Token Usage**: Input, output, and total token consumption tracking per repository analysis.
- **Test Execution Metrics**: Pass/fail rates, execution speed, and coverage trends.

---

## ⚠️ Graceful Data Fallbacks & Preview Banners

When metrics services or background workers are initializing or offline:
- **Sample Data Previews**: The monitoring dashboard renders sample metrics cards so the UI design can be evaluated without disruption.
- **Amber Warning Banners**: Distinct amber banners alert the user whenever sample/mock data is displayed.
