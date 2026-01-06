"""Unit tests for system log tools.

TDD: Write these tests FIRST, then implement src/tools/system_logs.py
Based on API endpoints:
- GET /proxy/network/v2/api/site/{site}/system-log/all
- GET /proxy/network/v2/api/site/{site}/system-log/count
- GET /proxy/network/v2/api/site/{site}/system-log/setting
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config import Settings


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = MagicMock(spec=Settings)
    settings.api_key = "test-api-key"
    settings.api_type = "local"
    settings.local_host = "192.168.1.1"
    settings.local_port = 443
    settings.local_verify_ssl = False
    settings.log_level = "INFO"
    return settings


@pytest.fixture
def sample_log_entries():
    """Sample log entries from captured schema."""
    return [
        {
            "id": "695aee313f84e073e5db5afe",
            "category": "SECURITY",
            "subcategory": "SECURITY_FIREWALL",
            "event": "BLOCKED_BY_FIREWALL",
            "severity": "MEDIUM",
            "status": "NEW",
            "timestamp": 1767566897127,
            "title_raw": "Blocked by Firewall",
            "message_raw": "{SRC_CLIENT} was blocked by {TRIGGER}",
            "parameters": {
                "SRC_CLIENT": {"id": "aa:bb:cc:dd:ee:ff", "name": "Test Client"},
                "TRIGGER": {"id": "rule1", "name": "Block Rule"},
            },
            "show_on_dashboard": False,
        },
        {
            "id": "695aee313f84e073e5db5aff",
            "category": "MONITORING",
            "subcategory": "MONITORING_WIFI",
            "event": "CLIENT_CONNECTED_WIRELESS",
            "severity": "LOW",
            "status": "NEW",
            "timestamp": 1767566890000,
            "title_raw": "Client Connected",
            "message_raw": "{CLIENT} connected to {SSID}",
            "parameters": {
                "CLIENT": {"id": "11:22:33:44:55:66", "name": "Phone"},
                "SSID": {"id": "wifi1", "name": "Main WiFi"},
            },
            "show_on_dashboard": False,
        },
    ]


@pytest.fixture
def sample_log_counts():
    """Sample log count response."""
    return {
        "events": [
            {"count": 1070, "name": "BLOCKED_BY_FIREWALL"},
            {"count": 672, "name": "CLIENT_CONNECTED_WIRELESS"},
            {"count": 677, "name": "CLIENT_DISCONNECTED_WIRELESS"},
        ],
        "subcategories": [
            {"count": 1070, "name": "SECURITY_FIREWALL"},
            {"count": 2066, "name": "MONITORING_WIFI"},
        ],
    }


@pytest.fixture
def sample_log_settings():
    """Sample log settings response."""
    return {
        "alert_event_settings": {
            "BLOCKED_BY_FIREWALL": {
                "category": "SECURITY",
                "subcategory": "SECURITY_FIREWALL",
                "label": "Blocked by Firewall",
                "send_email": False,
                "send_mobile_push_notification": False,
            },
            "CLIENT_CONNECTED_WIRELESS": {
                "category": "MONITORING",
                "subcategory": "MONITORING_WIFI",
                "label": "WiFi Client Connected",
                "send_email": False,
                "send_mobile_push_notification": False,
            },
        },
        "setting_preference": "ON",
    }


class TestListSystemLogs:
    """Tests for list_system_logs tool."""

    @pytest.mark.asyncio
    async def test_list_all_logs(self, mock_settings, sample_log_entries):
        """List logs without filters."""
        from src.tools.system_logs import list_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_log_entries})

            result = await list_system_logs("default", mock_settings)

            assert len(result) == 2
            assert result[0]["id"] == "695aee313f84e073e5db5afe"
            assert result[0]["category"] == "SECURITY"

    @pytest.mark.asyncio
    async def test_filter_by_category_security(self, mock_settings, sample_log_entries):
        """Filter logs to SECURITY category only."""
        from src.tools.system_logs import list_system_logs

        security_logs = [e for e in sample_log_entries if e["category"] == "SECURITY"]

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": security_logs})

            result = await list_system_logs("default", mock_settings, category="SECURITY")

            assert len(result) == 1
            assert result[0]["category"] == "SECURITY"

    @pytest.mark.asyncio
    async def test_filter_by_subcategory_firewall(self, mock_settings, sample_log_entries):
        """Filter logs to SECURITY_FIREWALL subcategory."""
        from src.tools.system_logs import list_system_logs

        firewall_logs = [e for e in sample_log_entries if e["subcategory"] == "SECURITY_FIREWALL"]

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": firewall_logs})

            result = await list_system_logs(
                "default", mock_settings, subcategory="SECURITY_FIREWALL"
            )

            assert len(result) == 1
            assert result[0]["subcategory"] == "SECURITY_FIREWALL"

    @pytest.mark.asyncio
    async def test_filter_by_severity_medium(self, mock_settings, sample_log_entries):
        """Filter logs to MEDIUM severity."""
        from src.tools.system_logs import list_system_logs

        medium_logs = [e for e in sample_log_entries if e["severity"] == "MEDIUM"]

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": medium_logs})

            result = await list_system_logs("default", mock_settings, severity="MEDIUM")

            assert len(result) == 1
            assert result[0]["severity"] == "MEDIUM"

    @pytest.mark.asyncio
    async def test_limit_results(self, mock_settings, sample_log_entries):
        """Verify limit parameter works correctly."""
        from src.tools.system_logs import list_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_log_entries[:1]})

            result = await list_system_logs("default", mock_settings, limit=1)

            assert len(result) == 1
            mock_instance.get.assert_called_once()
            call_args = mock_instance.get.call_args
            assert "limit" in call_args[1].get("params", {})

    @pytest.mark.asyncio
    async def test_time_range_24h(self, mock_settings, sample_log_entries):
        """Filter logs to last 24 hours."""
        from src.tools.system_logs import list_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_log_entries})

            result = await list_system_logs("default", mock_settings, time_range="24h")

            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_empty_response_handling(self, mock_settings):
        """Handle sites with no log entries."""
        from src.tools.system_logs import list_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": []})

            result = await list_system_logs("default", mock_settings)

            assert len(result) == 0
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_offset_parameter(self, mock_settings, sample_log_entries):
        """Verify offset parameter for pagination."""
        from src.tools.system_logs import list_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_log_entries[1:]})

            await list_system_logs("default", mock_settings, offset=1)

            mock_instance.get.assert_called_once()
            call_args = mock_instance.get.call_args
            assert "offset" in call_args[1].get("params", {})


class TestGetSystemLogCounts:
    """Tests for get_system_log_counts tool."""

    @pytest.mark.asyncio
    async def test_get_counts_all_categories(self, mock_settings, sample_log_counts):
        """Get counts for all event categories."""
        from src.tools.system_logs import get_system_log_counts

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_log_counts)

            result = await get_system_log_counts("default", mock_settings)

            assert "events" in result
            assert "subcategories" in result
            assert len(result["events"]) == 3
            assert len(result["subcategories"]) == 2

    @pytest.mark.asyncio
    async def test_verify_count_aggregation(self, mock_settings, sample_log_counts):
        """Verify events and subcategories are both returned."""
        from src.tools.system_logs import get_system_log_counts

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_log_counts)

            result = await get_system_log_counts("default", mock_settings)

            firewall_events = [e for e in result["events"] if e["name"] == "BLOCKED_BY_FIREWALL"]
            assert len(firewall_events) == 1
            assert firewall_events[0]["count"] == 1070

    @pytest.mark.asyncio
    async def test_firewall_block_count(self, mock_settings, sample_log_counts):
        """Verify BLOCKED_BY_FIREWALL count matches expected."""
        from src.tools.system_logs import get_system_log_counts

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_log_counts)

            result = await get_system_log_counts("default", mock_settings)

            firewall_count = next(
                (e["count"] for e in result["events"] if e["name"] == "BLOCKED_BY_FIREWALL"),
                0,
            )
            assert firewall_count == 1070

    @pytest.mark.asyncio
    async def test_empty_counts(self, mock_settings):
        """Handle empty count response."""
        from src.tools.system_logs import get_system_log_counts

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"events": [], "subcategories": []})

            result = await get_system_log_counts("default", mock_settings)

            assert len(result["events"]) == 0
            assert len(result["subcategories"]) == 0

    @pytest.mark.asyncio
    async def test_time_range_parameter(self, mock_settings, sample_log_counts):
        """Verify time_range parameter is passed to API."""
        from src.tools.system_logs import get_system_log_counts

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_log_counts)

            await get_system_log_counts("default", mock_settings, time_range="7d")

            mock_instance.get.assert_called_once()


class TestGetSystemLogSettings:
    """Tests for get_system_log_settings tool."""

    @pytest.mark.asyncio
    async def test_get_settings(self, mock_settings, sample_log_settings):
        """Retrieve all alert event settings."""
        from src.tools.system_logs import get_system_log_settings

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_log_settings)

            result = await get_system_log_settings("default", mock_settings)

            assert "alert_event_settings" in result
            assert "setting_preference" in result
            assert result["setting_preference"] == "ON"

    @pytest.mark.asyncio
    async def test_parse_all_alert_types(self, mock_settings, sample_log_settings):
        """Ensure all alert types are parsed correctly."""
        from src.tools.system_logs import get_system_log_settings

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_log_settings)

            result = await get_system_log_settings("default", mock_settings)

            assert "BLOCKED_BY_FIREWALL" in result["alert_event_settings"]
            assert "CLIENT_CONNECTED_WIRELESS" in result["alert_event_settings"]
            firewall_setting = result["alert_event_settings"]["BLOCKED_BY_FIREWALL"]
            assert firewall_setting["category"] == "SECURITY"

    @pytest.mark.asyncio
    async def test_notification_preferences(self, mock_settings, sample_log_settings):
        """Verify email/push notification settings."""
        from src.tools.system_logs import get_system_log_settings

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_log_settings)

            result = await get_system_log_settings("default", mock_settings)

            firewall_setting = result["alert_event_settings"]["BLOCKED_BY_FIREWALL"]
            assert firewall_setting["send_email"] is False
            assert firewall_setting["send_mobile_push_notification"] is False

    @pytest.mark.asyncio
    async def test_empty_settings(self, mock_settings):
        """Handle empty alert_event_settings."""
        from src.tools.system_logs import get_system_log_settings

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(
                return_value={"alert_event_settings": {}, "setting_preference": "OFF"}
            )

            result = await get_system_log_settings("default", mock_settings)

            assert len(result["alert_event_settings"]) == 0
            assert result["setting_preference"] == "OFF"


class TestSearchSystemLogs:
    """Tests for search_system_logs tool."""

    @pytest.mark.asyncio
    async def test_search_by_ip(self, mock_settings, sample_log_entries):
        """Search logs by IP address."""
        from src.tools.system_logs import search_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_log_entries})

            result = await search_system_logs("default", mock_settings, query="192.168.1.1")

            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_search_by_mac(self, mock_settings, sample_log_entries):
        """Search logs by MAC address."""
        from src.tools.system_logs import search_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_log_entries})

            result = await search_system_logs("default", mock_settings, query="aa:bb:cc:dd:ee:ff")

            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_search_by_client_name(self, mock_settings, sample_log_entries):
        """Search logs by client hostname/name."""
        from src.tools.system_logs import search_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_log_entries})

            result = await search_system_logs("default", mock_settings, query="Test Client")

            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_search_with_limit(self, mock_settings, sample_log_entries):
        """Search logs with result limit."""
        from src.tools.system_logs import search_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_log_entries[:1]})

            await search_system_logs("default", mock_settings, query="test", limit=1)

            mock_instance.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_empty_results(self, mock_settings):
        """Handle empty search results."""
        from src.tools.system_logs import search_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": []})

            result = await search_system_logs("default", mock_settings, query="nonexistent")

            assert len(result) == 0
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_search_case_insensitive(self, mock_settings, sample_log_entries):
        """Search should work case-insensitively on client-side filtering."""
        from src.tools.system_logs import search_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_log_entries})

            result = await search_system_logs("default", mock_settings, query="TEST CLIENT")

            assert isinstance(result, list)


class TestApiEndpoints:
    """Tests for API endpoint construction."""

    @pytest.mark.asyncio
    async def test_list_logs_endpoint(self, mock_settings, sample_log_entries):
        """Verify correct API endpoint for listing logs."""
        from src.tools.system_logs import list_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_log_entries})

            await list_system_logs("test-site", mock_settings)

            call_args = mock_instance.get.call_args
            endpoint = call_args[0][0]
            assert "system-log" in endpoint
            assert "test-site" in endpoint

    @pytest.mark.asyncio
    async def test_count_endpoint(self, mock_settings, sample_log_counts):
        """Verify correct API endpoint for counts."""
        from src.tools.system_logs import get_system_log_counts

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_log_counts)

            await get_system_log_counts("test-site", mock_settings)

            call_args = mock_instance.get.call_args
            endpoint = call_args[0][0]
            assert "system-log/count" in endpoint
            assert "test-site" in endpoint

    @pytest.mark.asyncio
    async def test_settings_endpoint(self, mock_settings, sample_log_settings):
        """Verify correct API endpoint for settings."""
        from src.tools.system_logs import get_system_log_settings

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_log_settings)

            await get_system_log_settings("test-site", mock_settings)

            call_args = mock_instance.get.call_args
            endpoint = call_args[0][0]
            assert "system-log/setting" in endpoint
            assert "test-site" in endpoint


class TestErrorHandling:
    """Tests for error handling in system log tools."""

    @pytest.mark.asyncio
    async def test_api_error_handling(self, mock_settings):
        """Handle API errors gracefully."""
        from src.tools.system_logs import list_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=Exception("API Error"))

            result = await list_system_logs("default", mock_settings)

            assert result == []

    @pytest.mark.asyncio
    async def test_authentication_called(self, mock_settings, sample_log_entries):
        """Verify authentication is called when not authenticated."""
        from src.tools.system_logs import list_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_log_entries})

            await list_system_logs("default", mock_settings)

            mock_instance.authenticate.assert_called_once()

    @pytest.mark.asyncio
    async def test_counts_api_error_handling(self, mock_settings):
        """Handle API errors in get_system_log_counts."""
        from src.tools.system_logs import get_system_log_counts

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=Exception("API Error"))

            result = await get_system_log_counts("default", mock_settings)

            assert result == {"events": [], "subcategories": []}

    @pytest.mark.asyncio
    async def test_settings_api_error_handling(self, mock_settings):
        """Handle API errors in get_system_log_settings."""
        from src.tools.system_logs import get_system_log_settings

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=Exception("API Error"))

            result = await get_system_log_settings("default", mock_settings)

            assert result == {"alert_event_settings": {}, "setting_preference": "OFF"}

    @pytest.mark.asyncio
    async def test_search_api_error_handling(self, mock_settings):
        """Handle API errors in search_system_logs."""
        from src.tools.system_logs import search_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=Exception("API Error"))

            result = await search_system_logs("default", mock_settings, query="test")

            assert result == []


class TestEventFiltering:
    """Tests for event type filtering in list_system_logs."""

    @pytest.mark.asyncio
    async def test_filter_by_event_type(self, mock_settings, sample_log_entries):
        """Filter logs by specific event type."""
        from src.tools.system_logs import list_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_log_entries[:1]})

            await list_system_logs("default", mock_settings, event="BLOCKED_BY_FIREWALL")

            call_args = mock_instance.get.call_args
            assert "event" in call_args[1].get("params", {})

    @pytest.mark.asyncio
    async def test_all_filter_parameters(self, mock_settings, sample_log_entries):
        """Test all filter parameters together."""
        from src.tools.system_logs import list_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_log_entries})

            await list_system_logs(
                "default",
                mock_settings,
                category="SECURITY",
                subcategory="SECURITY_FIREWALL",
                severity="MEDIUM",
                event="BLOCKED_BY_FIREWALL",
                time_range="24h",
                limit=10,
                offset=5,
            )

            call_args = mock_instance.get.call_args
            params = call_args[1].get("params", {})
            assert "category" in params
            assert "subcategory" in params
            assert "severity" in params
            assert "event" in params
            assert "timeRange" in params
            assert "limit" in params
            assert "offset" in params


class TestSearchFiltering:
    """Tests for search parameter matching logic."""

    @pytest.mark.asyncio
    async def test_search_matches_ip_in_parameters(self, mock_settings):
        """Search finds matches in parameter IP fields."""
        from src.tools.system_logs import search_system_logs

        entries = [
            {
                "id": "entry1",
                "category": "SECURITY",
                "subcategory": "SECURITY_FIREWALL",
                "event": "BLOCKED_BY_FIREWALL",
                "severity": "MEDIUM",
                "status": "NEW",
                "timestamp": 1767566897127,
                "title_raw": "Blocked",
                "message_raw": "Blocked by firewall",
                "parameters": {
                    "SRC_CLIENT": {
                        "id": "aa:bb:cc:dd:ee:ff",
                        "name": "Test",
                        "ip": "192.168.1.100",
                    }
                },
            }
        ]

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": entries})

            result = await search_system_logs("default", mock_settings, query="192.168.1.100")

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_matches_hostname_in_parameters(self, mock_settings):
        """Search finds matches in parameter hostname fields."""
        from src.tools.system_logs import search_system_logs

        entries = [
            {
                "id": "entry1",
                "category": "MONITORING",
                "subcategory": "MONITORING_WIFI",
                "event": "CLIENT_CONNECTED_WIRELESS",
                "severity": "LOW",
                "status": "NEW",
                "timestamp": 1767566897127,
                "title_raw": "Connected",
                "message_raw": "Client connected",
                "parameters": {
                    "CLIENT": {
                        "id": "aa:bb:cc:dd:ee:ff",
                        "name": "MyPhone",
                        "hostname": "johns-iphone",
                    }
                },
            }
        ]

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": entries})

            result = await search_system_logs("default", mock_settings, query="johns-iphone")

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_no_matches(self, mock_settings, sample_log_entries):
        """Search returns empty when no matches found."""
        from src.tools.system_logs import search_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_log_entries})

            result = await search_system_logs(
                "default", mock_settings, query="totally-unique-nonexistent-query"
            )

            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_search_with_time_range(self, mock_settings, sample_log_entries):
        """Search passes time_range parameter to API."""
        from src.tools.system_logs import search_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_log_entries})

            await search_system_logs("default", mock_settings, query="test", time_range="7d")

            call_args = mock_instance.get.call_args
            params = call_args[1].get("params", {})
            assert "timeRange" in params


class TestNonDictResponses:
    """Tests for handling non-dict responses from API."""

    @pytest.mark.asyncio
    async def test_list_logs_non_dict_response(self, mock_settings):
        """Handle non-dict response in list_system_logs."""
        from src.tools.system_logs import list_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=[])

            result = await list_system_logs("default", mock_settings)

            assert result == []

    @pytest.mark.asyncio
    async def test_counts_non_dict_response(self, mock_settings):
        """Handle non-dict response in get_system_log_counts."""
        from src.tools.system_logs import get_system_log_counts

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=[])

            result = await get_system_log_counts("default", mock_settings)

            assert "events" in result
            assert "subcategories" in result

    @pytest.mark.asyncio
    async def test_settings_non_dict_response(self, mock_settings):
        """Handle non-dict response in get_system_log_settings by triggering exception path."""
        from src.tools.system_logs import get_system_log_settings

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=Exception("Non-dict response"))

            result = await get_system_log_settings("default", mock_settings)

            assert result == {"alert_event_settings": {}, "setting_preference": "OFF"}

    @pytest.mark.asyncio
    async def test_search_non_dict_response(self, mock_settings):
        """Handle non-dict response in search_system_logs."""
        from src.tools.system_logs import search_system_logs

        with patch("src.tools.system_logs.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=[])

            result = await search_system_logs("default", mock_settings, query="test")

            assert result == []
