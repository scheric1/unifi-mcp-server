"""Unit tests for SystemLog models.

TDD: Write these tests FIRST, then implement src/models/system_log.py
Based on captured schemas in docs/research/schemas/system-log-*.json
"""

import pytest
from pydantic import ValidationError


class TestLogCategory:
    """Tests for LogCategory enum."""

    def test_security_value(self):
        """SECURITY should be a valid category."""
        from src.models.system_log import LogCategory

        assert LogCategory.SECURITY.value == "SECURITY"

    def test_system_value(self):
        """SYSTEM should be a valid category."""
        from src.models.system_log import LogCategory

        assert LogCategory.SYSTEM.value == "SYSTEM"

    def test_monitoring_value(self):
        """MONITORING should be a valid category."""
        from src.models.system_log import LogCategory

        assert LogCategory.MONITORING.value == "MONITORING"

    def test_internet_value(self):
        """INTERNET should be a valid category."""
        from src.models.system_log import LogCategory

        assert LogCategory.INTERNET.value == "INTERNET"

    def test_power_value(self):
        """POWER should be a valid category."""
        from src.models.system_log import LogCategory

        assert LogCategory.POWER.value == "POWER"

    def test_invalid_category_raises(self):
        """Invalid category should raise ValueError."""
        from src.models.system_log import LogCategory

        with pytest.raises(ValueError):
            LogCategory("INVALID")


class TestLogSeverity:
    """Tests for LogSeverity enum."""

    def test_low_value(self):
        """LOW should be a valid severity."""
        from src.models.system_log import LogSeverity

        assert LogSeverity.LOW.value == "LOW"

    def test_medium_value(self):
        """MEDIUM should be a valid severity."""
        from src.models.system_log import LogSeverity

        assert LogSeverity.MEDIUM.value == "MEDIUM"

    def test_high_value(self):
        """HIGH should be a valid severity."""
        from src.models.system_log import LogSeverity

        assert LogSeverity.HIGH.value == "HIGH"

    def test_critical_value(self):
        """CRITICAL should be a valid severity."""
        from src.models.system_log import LogSeverity

        assert LogSeverity.CRITICAL.value == "CRITICAL"


class TestLogStatus:
    """Tests for LogStatus enum."""

    def test_new_value(self):
        """NEW should be a valid status."""
        from src.models.system_log import LogStatus

        assert LogStatus.NEW.value == "NEW"

    def test_acknowledged_value(self):
        """ACKNOWLEDGED should be a valid status."""
        from src.models.system_log import LogStatus

        assert LogStatus.ACKNOWLEDGED.value == "ACKNOWLEDGED"

    def test_resolved_value(self):
        """RESOLVED should be a valid status."""
        from src.models.system_log import LogStatus

        assert LogStatus.RESOLVED.value == "RESOLVED"


class TestSettingPreference:
    """Tests for SettingPreference enum."""

    def test_on_value(self):
        """ON should be a valid preference."""
        from src.models.system_log import SettingPreference

        assert SettingPreference.ON.value == "ON"

    def test_off_value(self):
        """OFF should be a valid preference."""
        from src.models.system_log import SettingPreference

        assert SettingPreference.OFF.value == "OFF"

    def test_custom_value(self):
        """CUSTOM should be a valid preference."""
        from src.models.system_log import SettingPreference

        assert SettingPreference.CUSTOM.value == "CUSTOM"


class TestSystemLogEventParameter:
    """Tests for SystemLogEventParameter model."""

    def test_parse_basic_parameter(self):
        """Parse a basic parameter with id and name."""
        from src.models.system_log import SystemLogEventParameter

        data = {"id": "192.168.1.59", "name": "192.168.1.59"}
        param = SystemLogEventParameter(**data)
        assert param.id == "192.168.1.59"
        assert param.name == "192.168.1.59"
        assert param.ip is None
        assert param.hostname is None

    def test_parse_client_parameter(self):
        """Parse a client parameter with IP and hostname."""
        from src.models.system_log import SystemLogEventParameter

        data = {
            "id": "bc:24:11:4f:fd:2a",
            "name": "opencode fd:2a",
            "ip": "192.168.20.133",
            "hostname": "opencode",
        }
        param = SystemLogEventParameter(**data)
        assert param.id == "bc:24:11:4f:fd:2a"
        assert param.name == "opencode fd:2a"
        assert param.ip == "192.168.20.133"
        assert param.hostname == "opencode"

    def test_parse_parameter_with_fingerprint(self):
        """Parse a parameter with device fingerprint data."""
        from src.models.system_log import SystemLogEventParameter

        data = {
            "id": "58:47:ca:74:d8:72",
            "name": "serv-1 Proxmox Server",
            "ip": "192.168.20.10",
            "device_fingerprint_id": 5254,
            "fingerprint_source": 0,
        }
        param = SystemLogEventParameter(**data)
        assert param.device_fingerprint_id == 5254
        assert param.fingerprint_source == 0

    def test_parse_parameter_with_not_actionable(self):
        """Parse a parameter with not_actionable flag."""
        from src.models.system_log import SystemLogEventParameter

        data = {
            "id": "192.168.1.60",
            "name": "192.168.1.60",
            "not_actionable": True,
        }
        param = SystemLogEventParameter(**data)
        assert param.not_actionable is True

    def test_parameter_allows_extra_fields(self):
        """Model should allow extra fields from API."""
        from src.models.system_log import SystemLogEventParameter

        data = {"id": "test", "name": "test", "some_unknown_field": "value"}
        param = SystemLogEventParameter(**data)
        assert param.id == "test"


class TestSystemLogEntry:
    """Tests for SystemLogEntry model."""

    def test_parse_firewall_block_event(self):
        """Parse a real BLOCKED_BY_FIREWALL event from captured schema."""
        from src.models.system_log import SystemLogEntry

        data = {
            "id": "695aee313f84e073e5db5afe",
            "category": "SECURITY",
            "subcategory": "SECURITY_FIREWALL",
            "event": "BLOCKED_BY_FIREWALL",
            "severity": "MEDIUM",
            "status": "NEW",
            "timestamp": 1767566897127,
            "title_raw": "Blocked by Firewall",
            "message_raw": "{SRC_CLIENT} was blocked from accessing {DST_IP} by the {TRIGGER} Firewall Policy.",
            "parameters": {
                "SRC_CLIENT": {
                    "id": "58:47:ca:74:d8:72",
                    "name": "serv-1 Proxmox Server",
                    "ip": "192.168.20.10",
                },
                "DST_IP": {
                    "id": "192.168.1.60",
                    "name": "192.168.1.60",
                    "not_actionable": True,
                },
                "TRIGGER": {
                    "id": "682a0e42220317278bb0b2cb",
                    "name": "Block IOT → All_Internal",
                },
            },
            "show_on_dashboard": False,
            "target": "TRIGGER",
            "type": "CONTENT_FILTERING_AND_RESTRICTIONS",
        }
        entry = SystemLogEntry(**data)
        assert entry.id == "695aee313f84e073e5db5afe"
        assert entry.category == "SECURITY"
        assert entry.subcategory == "SECURITY_FIREWALL"
        assert entry.event == "BLOCKED_BY_FIREWALL"
        assert entry.severity == "MEDIUM"
        assert entry.status == "NEW"
        assert entry.timestamp == 1767566897127
        assert entry.title_raw == "Blocked by Firewall"
        assert entry.show_on_dashboard is False
        assert entry.target == "TRIGGER"
        assert entry.type == "CONTENT_FILTERING_AND_RESTRICTIONS"
        # Check parameters are parsed
        assert "SRC_CLIENT" in entry.parameters
        assert entry.parameters["SRC_CLIENT"].ip == "192.168.20.10"

    def test_parse_client_connected_event(self):
        """Parse CLIENT_CONNECTED_WIRELESS event."""
        from src.models.system_log import SystemLogEntry

        data = {
            "id": "abc123",
            "category": "MONITORING",
            "subcategory": "MONITORING_WIFI",
            "event": "CLIENT_CONNECTED_WIRELESS",
            "severity": "LOW",
            "status": "NEW",
            "timestamp": 1767566000000,
            "title_raw": "WiFi Client Connected",
            "message_raw": "{CLIENT} connected to {SSID}",
            "parameters": {
                "CLIENT": {"id": "aa:bb:cc:dd:ee:ff", "name": "My Phone"},
                "SSID": {"id": "main-wifi", "name": "Main WiFi"},
            },
        }
        entry = SystemLogEntry(**data)
        assert entry.category == "MONITORING"
        assert entry.event == "CLIENT_CONNECTED_WIRELESS"

    def test_severity_validation(self):
        """Ensure only valid severity levels accepted."""
        from src.models.system_log import SystemLogEntry

        with pytest.raises(ValidationError):
            SystemLogEntry(
                id="test",
                category="SECURITY",
                subcategory="TEST",
                event="TEST",
                severity="INVALID",  # Invalid severity
                status="NEW",
                timestamp=123456789,
                title_raw="Test",
                message_raw="Test",
                parameters={},
            )

    def test_category_validation(self):
        """Ensure only valid categories accepted."""
        from src.models.system_log import SystemLogEntry

        with pytest.raises(ValidationError):
            SystemLogEntry(
                id="test",
                category="INVALID",  # Invalid category
                subcategory="TEST",
                event="TEST",
                severity="LOW",
                status="NEW",
                timestamp=123456789,
                title_raw="Test",
                message_raw="Test",
                parameters={},
            )

    def test_status_validation(self):
        """Ensure only valid status values accepted."""
        from src.models.system_log import SystemLogEntry

        with pytest.raises(ValidationError):
            SystemLogEntry(
                id="test",
                category="SECURITY",
                subcategory="TEST",
                event="TEST",
                severity="LOW",
                status="INVALID",  # Invalid status
                timestamp=123456789,
                title_raw="Test",
                message_raw="Test",
                parameters={},
            )

    def test_optional_fields_default(self):
        """Optional fields should have sensible defaults."""
        from src.models.system_log import SystemLogEntry

        data = {
            "id": "test",
            "category": "SECURITY",
            "subcategory": "TEST",
            "event": "TEST",
            "severity": "LOW",
            "status": "NEW",
            "timestamp": 123456789,
            "title_raw": "Test",
            "message_raw": "Test",
            "parameters": {},
        }
        entry = SystemLogEntry(**data)
        assert entry.show_on_dashboard is False
        assert entry.target is None
        assert entry.type is None
        assert entry.key is None

    def test_model_allows_extra_fields(self):
        """Model should allow extra fields from API."""
        from src.models.system_log import SystemLogEntry

        data = {
            "id": "test",
            "category": "SECURITY",
            "subcategory": "TEST",
            "event": "TEST",
            "severity": "LOW",
            "status": "NEW",
            "timestamp": 123456789,
            "title_raw": "Test",
            "message_raw": "Test",
            "parameters": {},
            "unknown_future_field": "value",
        }
        entry = SystemLogEntry(**data)
        assert entry.id == "test"


class TestSystemLogCount:
    """Tests for SystemLogCount model."""

    def test_parse_event_count(self):
        """Parse event count data."""
        from src.models.system_log import SystemLogCount

        data = {"name": "BLOCKED_BY_FIREWALL", "count": 1070}
        count = SystemLogCount(**data)
        assert count.name == "BLOCKED_BY_FIREWALL"
        assert count.count == 1070

    def test_parse_subcategory_count(self):
        """Parse subcategory count data."""
        from src.models.system_log import SystemLogCount

        data = {"name": "SECURITY_FIREWALL", "count": 1070}
        count = SystemLogCount(**data)
        assert count.name == "SECURITY_FIREWALL"
        assert count.count == 1070

    def test_count_must_be_integer(self):
        """Count must be an integer."""
        from src.models.system_log import SystemLogCount

        # Should handle string numbers via coercion
        data = {"name": "TEST", "count": "100"}
        count = SystemLogCount(**data)
        assert count.count == 100


class TestSystemLogCountResponse:
    """Tests for SystemLogCountResponse model."""

    def test_parse_count_response(self):
        """Parse the captured system-log-count.json response."""
        from src.models.system_log import SystemLogCountResponse

        data = {
            "events": [
                {"count": 34, "name": "CLIENT_DISCONNECTED_WIRED"},
                {"count": 672, "name": "CLIENT_CONNECTED_WIRELESS"},
                {"count": 677, "name": "CLIENT_DISCONNECTED_WIRELESS"},
                {"count": 1070, "name": "BLOCKED_BY_FIREWALL"},
                {"count": 717, "name": "CLIENT_ROAMED"},
                {"count": 60, "name": "ADMIN_ACCESS"},
                {"count": 10, "name": "CLIENT_CONNECTED_WIRED"},
            ],
            "subcategories": [
                {"count": 1070, "name": "SECURITY_FIREWALL"},
                {"count": 60, "name": "SYSTEM_ADMIN"},
                {"count": 2066, "name": "MONITORING_WIFI"},
                {"count": 44, "name": "MONITORING_WIRED"},
            ],
        }
        response = SystemLogCountResponse(**data)
        assert len(response.events) == 7
        assert len(response.subcategories) == 4
        # Verify specific counts
        firewall_events = [e for e in response.events if e.name == "BLOCKED_BY_FIREWALL"]
        assert len(firewall_events) == 1
        assert firewall_events[0].count == 1070

    def test_empty_counts(self):
        """Handle empty count arrays."""
        from src.models.system_log import SystemLogCountResponse

        data = {"events": [], "subcategories": []}
        response = SystemLogCountResponse(**data)
        assert len(response.events) == 0
        assert len(response.subcategories) == 0

    def test_get_total_events(self):
        """Verify total events calculation works."""
        from src.models.system_log import SystemLogCountResponse

        data = {
            "events": [
                {"count": 100, "name": "EVENT_A"},
                {"count": 200, "name": "EVENT_B"},
            ],
            "subcategories": [],
        }
        response = SystemLogCountResponse(**data)
        total = sum(e.count for e in response.events)
        assert total == 300


class TestAlertEventSetting:
    """Tests for AlertEventSetting model."""

    def test_parse_security_setting(self):
        """Parse a security alert event setting."""
        from src.models.system_log import AlertEventSetting

        data = {
            "category": "SECURITY",
            "subcategory": "SECURITY_FIREWALL",
            "label": "Blocked by Firewall",
            "send_email": False,
            "send_mobile_push_notification": False,
        }
        setting = AlertEventSetting(**data)
        assert setting.category == "SECURITY"
        assert setting.subcategory == "SECURITY_FIREWALL"
        assert setting.label == "Blocked by Firewall"
        assert setting.send_email is False
        assert setting.send_mobile_push_notification is False

    def test_parse_setting_with_notifications_enabled(self):
        """Parse setting with notifications enabled."""
        from src.models.system_log import AlertEventSetting

        data = {
            "category": "SYSTEM",
            "subcategory": "SYSTEM_DEVICES",
            "label": "Device Adopted",
            "send_email": False,
            "send_mobile_push_notification": True,
        }
        setting = AlertEventSetting(**data)
        assert setting.send_mobile_push_notification is True

    def test_default_notification_values(self):
        """Default notification values should be False."""
        from src.models.system_log import AlertEventSetting

        data = {
            "category": "SYSTEM",
            "subcategory": "TEST",
            "label": "Test",
        }
        setting = AlertEventSetting(**data)
        assert setting.send_email is False
        assert setting.send_mobile_push_notification is False


class TestSystemLogSettings:
    """Tests for SystemLogSettings model."""

    def test_parse_settings_response(self):
        """Parse a subset of the captured system-log-setting.json response."""
        from src.models.system_log import SystemLogSettings

        data = {
            "alert_event_settings": {
                "ADMIN_ACCESS": {
                    "category": "SYSTEM",
                    "label": "Admin Accessed UniFi Network",
                    "send_email": False,
                    "send_mobile_push_notification": False,
                    "subcategory": "SYSTEM_ADMIN",
                },
                "BLOCKED_BY_FIREWALL": {
                    "category": "SECURITY",
                    "label": "Blocked by Firewall",
                    "send_email": False,
                    "send_mobile_push_notification": False,
                    "subcategory": "SECURITY_FIREWALL",
                },
                "DEVICE_ADOPTED": {
                    "category": "SYSTEM",
                    "label": "Device Adopted",
                    "send_email": False,
                    "send_mobile_push_notification": True,
                    "subcategory": "SYSTEM_DEVICES",
                },
            },
            "setting_preference": "ON",
        }
        settings = SystemLogSettings(**data)
        assert len(settings.alert_event_settings) == 3
        assert settings.setting_preference == "ON"
        # Check specific settings
        assert "BLOCKED_BY_FIREWALL" in settings.alert_event_settings
        assert settings.alert_event_settings["BLOCKED_BY_FIREWALL"].category == "SECURITY"

    def test_setting_preference_validation(self):
        """Validate setting_preference enum values."""
        from src.models.system_log import SystemLogSettings

        data = {"alert_event_settings": {}, "setting_preference": "CUSTOM"}
        settings = SystemLogSettings(**data)
        assert settings.setting_preference == "CUSTOM"

    def test_invalid_setting_preference_raises(self):
        """Invalid setting_preference should raise ValidationError."""
        from src.models.system_log import SystemLogSettings

        with pytest.raises(ValidationError):
            SystemLogSettings(alert_event_settings={}, setting_preference="INVALID")

    def test_filter_by_category(self):
        """Filter settings by category."""
        from src.models.system_log import SystemLogSettings

        data = {
            "alert_event_settings": {
                "ADMIN_ACCESS": {
                    "category": "SYSTEM",
                    "label": "Admin Access",
                    "subcategory": "SYSTEM_ADMIN",
                },
                "BLOCKED_BY_FIREWALL": {
                    "category": "SECURITY",
                    "label": "Blocked",
                    "subcategory": "SECURITY_FIREWALL",
                },
                "CLIENT_CONNECTED_WIRELESS": {
                    "category": "MONITORING",
                    "label": "Client Connected",
                    "subcategory": "MONITORING_WIFI",
                },
            },
            "setting_preference": "ON",
        }
        settings = SystemLogSettings(**data)
        # Filter to get only SECURITY category settings
        security_settings = {
            k: v for k, v in settings.alert_event_settings.items() if v.category == "SECURITY"
        }
        assert len(security_settings) == 1
        assert "BLOCKED_BY_FIREWALL" in security_settings

    def test_empty_settings(self):
        """Handle empty alert_event_settings."""
        from src.models.system_log import SystemLogSettings

        data = {"alert_event_settings": {}, "setting_preference": "OFF"}
        settings = SystemLogSettings(**data)
        assert len(settings.alert_event_settings) == 0


class TestSystemLogEntryList:
    """Tests for SystemLogEntryList response wrapper model."""

    def test_parse_list_response(self):
        """Parse a list of system log entries."""
        from src.models.system_log import SystemLogEntryList

        data = {
            "data": [
                {
                    "id": "entry1",
                    "category": "SECURITY",
                    "subcategory": "SECURITY_FIREWALL",
                    "event": "BLOCKED_BY_FIREWALL",
                    "severity": "MEDIUM",
                    "status": "NEW",
                    "timestamp": 1767566897127,
                    "title_raw": "Blocked",
                    "message_raw": "Test",
                    "parameters": {},
                },
                {
                    "id": "entry2",
                    "category": "MONITORING",
                    "subcategory": "MONITORING_WIFI",
                    "event": "CLIENT_CONNECTED_WIRELESS",
                    "severity": "LOW",
                    "status": "NEW",
                    "timestamp": 1767566897000,
                    "title_raw": "Connected",
                    "message_raw": "Test",
                    "parameters": {},
                },
            ]
        }
        response = SystemLogEntryList(**data)
        assert len(response.data) == 2
        assert response.data[0].id == "entry1"
        assert response.data[1].id == "entry2"

    def test_empty_list(self):
        """Handle empty data list."""
        from src.models.system_log import SystemLogEntryList

        data = {"data": []}
        response = SystemLogEntryList(**data)
        assert len(response.data) == 0
