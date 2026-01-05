"""Unit tests for alarm management models.

TDD: Write these tests FIRST, then implement in src/models/alarm.py
Based on endpoints:
- GET /api/v2/alarms/network
- GET /api/v2/alarms/network/manifest
- GET /proxy/network/v2/api/alarm-manager/scope/sites
- GET /proxy/network/v2/api/alarm-manager/scope/devices
- GET /proxy/network/v2/api/alarm-manager/scope/clients
"""

import pytest
from pydantic import ValidationError


class TestAlarmSeverity:
    def test_critical_value(self):
        from src.models.alarm import AlarmSeverity

        assert AlarmSeverity.CRITICAL.value == "critical"

    def test_warning_value(self):
        from src.models.alarm import AlarmSeverity

        assert AlarmSeverity.WARNING.value == "warning"

    def test_info_value(self):
        from src.models.alarm import AlarmSeverity

        assert AlarmSeverity.INFO.value == "info"

    def test_invalid_severity_raises(self):
        from src.models.alarm import AlarmSeverity

        with pytest.raises(ValueError):
            AlarmSeverity("invalid")


class TestAlarmStatus:
    def test_active_value(self):
        from src.models.alarm import AlarmStatus

        assert AlarmStatus.ACTIVE.value == "active"

    def test_acknowledged_value(self):
        from src.models.alarm import AlarmStatus

        assert AlarmStatus.ACKNOWLEDGED.value == "acknowledged"

    def test_resolved_value(self):
        from src.models.alarm import AlarmStatus

        assert AlarmStatus.RESOLVED.value == "resolved"


class TestAlarmScope:
    def test_site_value(self):
        from src.models.alarm import AlarmScope

        assert AlarmScope.SITE.value == "site"

    def test_device_value(self):
        from src.models.alarm import AlarmScope

        assert AlarmScope.DEVICE.value == "device"

    def test_client_value(self):
        from src.models.alarm import AlarmScope

        assert AlarmScope.CLIENT.value == "client"


class TestAlarmCategory:
    def test_connectivity_value(self):
        from src.models.alarm import AlarmCategory

        assert AlarmCategory.CONNECTIVITY.value == "connectivity"

    def test_performance_value(self):
        from src.models.alarm import AlarmCategory

        assert AlarmCategory.PERFORMANCE.value == "performance"

    def test_security_value(self):
        from src.models.alarm import AlarmCategory

        assert AlarmCategory.SECURITY.value == "security"

    def test_hardware_value(self):
        from src.models.alarm import AlarmCategory

        assert AlarmCategory.HARDWARE.value == "hardware"

    def test_configuration_value(self):
        from src.models.alarm import AlarmCategory

        assert AlarmCategory.CONFIGURATION.value == "configuration"


class TestAlarm:
    def test_parse_minimal(self):
        from src.models.alarm import Alarm

        data = {
            "_id": "alarm-123",
            "key": "device.offline",
            "severity": "critical",
            "message": "Device is offline",
            "timestamp": 1700000000000,
        }
        alarm = Alarm(**data)

        assert alarm.id == "alarm-123"
        assert alarm.key == "device.offline"
        assert alarm.severity == "critical"
        assert alarm.message == "Device is offline"
        assert alarm.acknowledged is False

    def test_parse_full(self):
        from src.models.alarm import Alarm

        data = {
            "_id": "alarm-123",
            "key": "device.offline",
            "severity": "critical",
            "status": "acknowledged",
            "message": "Device is offline",
            "timestamp": 1700000000000,
            "siteId": "site-abc",
            "deviceMac": "00:11:22:33:44:55",
            "clientMac": None,
            "acknowledged": True,
            "acknowledgedAt": 1700001000000,
            "acknowledgedBy": "admin@example.com",
            "resolved": False,
            "resolvedAt": None,
            "details": {"lastSeen": 1699999000000},
        }
        alarm = Alarm(**data)

        assert alarm.site_id == "site-abc"
        assert alarm.device_mac == "00:11:22:33:44:55"
        assert alarm.acknowledged is True
        assert alarm.acknowledged_by == "admin@example.com"
        assert alarm.details == {"lastSeen": 1699999000000}

    def test_allows_extra_fields(self):
        from src.models.alarm import Alarm

        data = {
            "_id": "alarm-123",
            "key": "test",
            "severity": "info",
            "message": "Test",
            "timestamp": 1700000000000,
            "unknownField": "value",
        }
        alarm = Alarm(**data)
        assert alarm.id == "alarm-123"


class TestAlarmScopeSettings:
    def test_parse_minimal(self):
        from src.models.alarm import AlarmScopeSettings

        data = {"scope": "site"}
        settings = AlarmScopeSettings(**data)

        assert settings.scope == "site"
        assert settings.enabled is True
        assert settings.notification_email is False

    def test_parse_full(self):
        from src.models.alarm import AlarmScopeSettings

        data = {
            "scope": "device",
            "enabled": True,
            "notificationEmail": True,
            "notificationPush": True,
            "thresholds": {"cpu_percent": 90, "memory_percent": 85},
        }
        settings = AlarmScopeSettings(**data)

        assert settings.scope == "device"
        assert settings.notification_email is True
        assert settings.notification_push is True
        assert settings.thresholds["cpu_percent"] == 90


class TestAlarmManifestEntry:
    def test_parse_minimal(self):
        from src.models.alarm import AlarmManifestEntry

        data = {
            "key": "device.offline",
            "name": "Device Offline",
            "severity": "critical",
        }
        entry = AlarmManifestEntry(**data)

        assert entry.key == "device.offline"
        assert entry.name == "Device Offline"
        assert entry.configurable is True

    def test_parse_full(self):
        from src.models.alarm import AlarmManifestEntry

        data = {
            "key": "client.poor_signal",
            "name": "Poor Client Signal",
            "description": "Client has poor wireless signal",
            "severity": "warning",
            "category": "performance",
            "configurable": True,
        }
        entry = AlarmManifestEntry(**data)

        assert entry.description == "Client has poor wireless signal"
        assert entry.category == "performance"


class TestAlarmManifest:
    def test_parse_empty(self):
        from src.models.alarm import AlarmManifest

        data = {"alarms": []}
        manifest = AlarmManifest(**data)

        assert manifest.alarms == []

    def test_parse_with_entries(self):
        from src.models.alarm import AlarmManifest

        data = {
            "alarms": [
                {"key": "device.offline", "name": "Device Offline", "severity": "critical"},
                {"key": "client.blocked", "name": "Client Blocked", "severity": "info"},
            ],
            "version": "1.0.0",
        }
        manifest = AlarmManifest(**data)

        assert len(manifest.alarms) == 2
        assert manifest.version == "1.0.0"
        assert manifest.alarms[0].key == "device.offline"


class TestAlarmListResponse:
    def test_parse_empty(self):
        from src.models.alarm import AlarmListResponse

        data = {"alarms": []}
        response = AlarmListResponse(**data)

        assert response.alarms == []
        assert response.total == 0
        assert response.active_count == 0

    def test_parse_with_alarms(self):
        from src.models.alarm import AlarmListResponse

        data = {
            "alarms": [
                {
                    "_id": "alarm-1",
                    "key": "device.offline",
                    "severity": "critical",
                    "message": "Device offline",
                    "timestamp": 1700000000000,
                }
            ],
            "total": 10,
            "activeCount": 5,
            "criticalCount": 2,
            "warningCount": 3,
        }
        response = AlarmListResponse(**data)

        assert len(response.alarms) == 1
        assert response.total == 10
        assert response.active_count == 5
        assert response.critical_count == 2
        assert response.warning_count == 3


class TestAlarmSummary:
    def test_parse_minimal(self):
        from src.models.alarm import AlarmSummary

        data = {"siteId": "site-abc"}
        summary = AlarmSummary(**data)

        assert summary.site_id == "site-abc"
        assert summary.total_alarms == 0
        assert summary.active_alarms == 0

    def test_parse_full(self):
        from src.models.alarm import AlarmSummary

        data = {
            "siteId": "site-abc",
            "totalAlarms": 50,
            "activeAlarms": 25,
            "criticalAlarms": 5,
            "warningAlarms": 15,
            "acknowledgedAlarms": 10,
            "deviceAlarms": 20,
            "clientAlarms": 5,
            "connectivityAlarms": 8,
            "oldestActive": 1699000000000,
        }
        summary = AlarmSummary(**data)

        assert summary.total_alarms == 50
        assert summary.active_alarms == 25
        assert summary.critical_alarms == 5
        assert summary.device_alarms == 20
        assert summary.oldest_active == 1699000000000


class TestAlarmAcknowledgement:
    def test_parse_minimal(self):
        from src.models.alarm import AlarmAcknowledgement

        data = {"alarmId": "alarm-123"}
        ack = AlarmAcknowledgement(**data)

        assert ack.alarm_id == "alarm-123"
        assert ack.acknowledged is True
        assert ack.note is None

    def test_parse_full(self):
        from src.models.alarm import AlarmAcknowledgement

        data = {
            "alarmId": "alarm-123",
            "acknowledged": True,
            "note": "Maintenance scheduled",
            "timestamp": 1700001000000,
        }
        ack = AlarmAcknowledgement(**data)

        assert ack.note == "Maintenance scheduled"
        assert ack.timestamp == 1700001000000


class TestModelConfigConsistency:
    def test_all_models_allow_extra(self):
        from src.models.alarm import (
            Alarm,
            AlarmAcknowledgement,
            AlarmListResponse,
            AlarmManifest,
            AlarmManifestEntry,
            AlarmScopeSettings,
            AlarmSummary,
        )

        models = [
            Alarm,
            AlarmScopeSettings,
            AlarmManifestEntry,
            AlarmManifest,
            AlarmListResponse,
            AlarmSummary,
            AlarmAcknowledgement,
        ]

        for model in models:
            config = model.model_config
            assert config.get("extra") == "allow", f"{model.__name__} should allow extra fields"
            assert config.get("populate_by_name") is True, (
                f"{model.__name__} should populate_by_name"
            )
