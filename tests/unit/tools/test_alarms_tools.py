"""Unit tests for alarm management tools.

TDD: Write these tests FIRST, then implement src/tools/alarms.py
Based on API endpoints:
- GET /api/v2/alarms/network
- GET /api/v2/alarms/network/manifest
- GET /proxy/network/v2/api/alarm-manager/scope/sites
- GET /proxy/network/v2/api/alarm-manager/scope/devices
- GET /proxy/network/v2/api/alarm-manager/scope/clients
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config import Settings


@pytest.fixture
def mock_settings():
    settings = MagicMock(spec=Settings)
    settings.api_key = "test-api-key"
    settings.api_type = "local"
    settings.local_host = "192.168.1.1"
    settings.local_port = 443
    settings.local_verify_ssl = False
    settings.log_level = "INFO"
    return settings


@pytest.fixture
def sample_alarms():
    return [
        {
            "_id": "alarm-1",
            "key": "device.offline",
            "severity": "critical",
            "status": "active",
            "message": "Device AP-Office is offline",
            "timestamp": 1700000000000,
            "deviceMac": "00:11:22:33:44:55",
            "acknowledged": False,
        },
        {
            "_id": "alarm-2",
            "key": "client.poor_signal",
            "severity": "warning",
            "status": "active",
            "message": "Client has poor signal",
            "timestamp": 1700001000000,
            "clientMac": "aa:bb:cc:dd:ee:ff",
            "acknowledged": False,
        },
        {
            "_id": "alarm-3",
            "key": "site.high_latency",
            "severity": "warning",
            "status": "acknowledged",
            "message": "High WAN latency detected",
            "timestamp": 1699999000000,
            "acknowledged": True,
            "acknowledgedAt": 1700000500000,
        },
    ]


@pytest.fixture
def sample_manifest():
    return {
        "alarms": [
            {
                "key": "device.offline",
                "name": "Device Offline",
                "description": "A device has gone offline",
                "severity": "critical",
                "category": "connectivity",
            },
            {
                "key": "client.poor_signal",
                "name": "Poor Client Signal",
                "description": "Client has poor wireless signal",
                "severity": "warning",
                "category": "performance",
            },
            {
                "key": "site.high_latency",
                "name": "High WAN Latency",
                "description": "WAN connection has high latency",
                "severity": "warning",
                "category": "performance",
            },
        ],
        "version": "1.0.0",
    }


@pytest.fixture
def sample_scope_settings():
    return {
        "sites": {"enabled": True, "notificationEmail": True, "notificationPush": True},
        "devices": {"enabled": True, "notificationEmail": True, "notificationPush": False},
        "clients": {"enabled": False, "notificationEmail": False, "notificationPush": False},
    }


class TestListAlarms:
    @pytest.mark.asyncio
    async def test_list_all_alarms(self, mock_settings, sample_alarms):
        from src.tools.alarms import list_alarms

        with patch("src.tools.alarms.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_alarms)

            result = await list_alarms("default", mock_settings)

            assert "alarms" in result
            assert len(result["alarms"]) == 3

    @pytest.mark.asyncio
    async def test_list_alarms_filter_severity(self, mock_settings, sample_alarms):
        from src.tools.alarms import list_alarms

        with patch("src.tools.alarms.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_alarms)

            result = await list_alarms("default", mock_settings, severity="critical")

            assert "alarms" in result
            assert all(a["severity"] == "critical" for a in result["alarms"])

    @pytest.mark.asyncio
    async def test_list_alarms_filter_status(self, mock_settings, sample_alarms):
        from src.tools.alarms import list_alarms

        with patch("src.tools.alarms.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_alarms)

            result = await list_alarms("default", mock_settings, status="active")

            assert "alarms" in result
            assert all(a["status"] == "active" for a in result["alarms"])

    @pytest.mark.asyncio
    async def test_list_alarms_empty(self, mock_settings):
        from src.tools.alarms import list_alarms

        with patch("src.tools.alarms.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=[])

            result = await list_alarms("default", mock_settings)

            assert result["alarms"] == []


class TestGetAlarmManifest:
    @pytest.mark.asyncio
    async def test_get_manifest(self, mock_settings, sample_manifest):
        from src.tools.alarms import get_alarm_manifest

        with patch("src.tools.alarms.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_manifest)

            result = await get_alarm_manifest(mock_settings)

            assert "alarms" in result
            assert len(result["alarms"]) == 3
            assert result["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_get_manifest_empty(self, mock_settings):
        from src.tools.alarms import get_alarm_manifest

        with patch("src.tools.alarms.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"alarms": []})

            result = await get_alarm_manifest(mock_settings)

            assert result["alarms"] == []


class TestGetAlarmSettings:
    @pytest.mark.asyncio
    async def test_get_site_settings(self, mock_settings, sample_scope_settings):
        from src.tools.alarms import get_alarm_settings

        with patch("src.tools.alarms.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_scope_settings["sites"])

            result = await get_alarm_settings("default", mock_settings, scope="sites")

            assert result["enabled"] is True
            assert result["notificationEmail"] is True

    @pytest.mark.asyncio
    async def test_get_device_settings(self, mock_settings, sample_scope_settings):
        from src.tools.alarms import get_alarm_settings

        with patch("src.tools.alarms.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_scope_settings["devices"])

            result = await get_alarm_settings("default", mock_settings, scope="devices")

            assert result["enabled"] is True

    @pytest.mark.asyncio
    async def test_get_client_settings(self, mock_settings, sample_scope_settings):
        from src.tools.alarms import get_alarm_settings

        with patch("src.tools.alarms.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_scope_settings["clients"])

            result = await get_alarm_settings("default", mock_settings, scope="clients")

            assert result["enabled"] is False


class TestAcknowledgeAlarm:
    @pytest.mark.asyncio
    async def test_acknowledge_alarm(self, mock_settings):
        from src.tools.alarms import acknowledge_alarm

        with patch("src.tools.alarms.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.post = AsyncMock(return_value={"success": True})

            result = await acknowledge_alarm("default", mock_settings, "alarm-123", confirm=True)

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_acknowledge_alarm_with_note(self, mock_settings):
        from src.tools.alarms import acknowledge_alarm

        with patch("src.tools.alarms.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.post = AsyncMock(return_value={"success": True})

            result = await acknowledge_alarm(
                "default",
                mock_settings,
                "alarm-123",
                note="Scheduled maintenance",
                confirm=True,
            )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_acknowledge_alarm_requires_confirm(self, mock_settings):
        from src.tools.alarms import acknowledge_alarm
        from src.utils.exceptions import ValidationError

        with pytest.raises(ValidationError):
            await acknowledge_alarm("default", mock_settings, "alarm-123", confirm=False)

    @pytest.mark.asyncio
    async def test_acknowledge_alarm_dry_run(self, mock_settings):
        from src.tools.alarms import acknowledge_alarm

        result = await acknowledge_alarm(
            "default", mock_settings, "alarm-123", confirm=True, dry_run=True
        )

        assert result["dry_run"] is True
        assert result["would_acknowledge"] == "alarm-123"


class TestGetAlarmSummary:
    @pytest.mark.asyncio
    async def test_get_alarm_summary(self, mock_settings, sample_alarms):
        from src.tools.alarms import get_alarm_summary

        with patch("src.tools.alarms.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_alarms)

            result = await get_alarm_summary("default", mock_settings)

            assert "total_alarms" in result
            assert "critical_alarms" in result
            assert "warning_alarms" in result
            assert result["total_alarms"] == 3

    @pytest.mark.asyncio
    async def test_alarm_summary_counts(self, mock_settings, sample_alarms):
        from src.tools.alarms import get_alarm_summary

        with patch("src.tools.alarms.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_alarms)

            result = await get_alarm_summary("default", mock_settings)

            assert result["critical_alarms"] == 1
            assert result["warning_alarms"] == 2
            assert result["active_alarms"] == 2
            assert result["acknowledged_alarms"] == 1

    @pytest.mark.asyncio
    async def test_alarm_summary_empty(self, mock_settings):
        from src.tools.alarms import get_alarm_summary

        with patch("src.tools.alarms.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=[])

            result = await get_alarm_summary("default", mock_settings)

            assert result["total_alarms"] == 0
            assert result["critical_alarms"] == 0


class TestInputValidation:
    @pytest.mark.asyncio
    async def test_invalid_site_id(self, mock_settings):
        from src.tools.alarms import list_alarms
        from src.utils.exceptions import ValidationError

        with pytest.raises(ValidationError):
            await list_alarms("", mock_settings)

    @pytest.mark.asyncio
    async def test_invalid_scope(self, mock_settings):
        from src.tools.alarms import get_alarm_settings
        from src.utils.exceptions import ValidationError

        with pytest.raises(ValidationError):
            await get_alarm_settings("default", mock_settings, scope="invalid")
