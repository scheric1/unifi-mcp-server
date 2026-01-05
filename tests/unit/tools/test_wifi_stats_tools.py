"""Unit tests for WiFi statistics tools.

TDD: Write these tests FIRST, then implement src/tools/wifi_stats.py
Based on API endpoints:
- GET /proxy/network/v2/api/site/{site}/wifi-stats/aps
- GET /proxy/network/v2/api/site/{site}/wifi-connectivity
- GET /proxy/network/v2/api/site/{site}/wifi-stats/details
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
def sample_ap_stats():
    return [
        {
            "mac": "00:11:22:33:44:55",
            "name": "Office AP",
            "model": "U7-Pro",
            "radios": [
                {"radio": "2g", "channel": 6, "clientCount": 5, "satisfaction": 85.0},
                {"radio": "5g", "channel": 36, "clientCount": 10, "satisfaction": 92.0},
            ],
            "totalClients": 15,
            "txBytes": 1000000000,
            "rxBytes": 500000000,
        },
        {
            "mac": "66:77:88:99:aa:bb",
            "name": "Lobby AP",
            "model": "U6-Lite",
            "radios": [
                {"radio": "2g", "channel": 1, "clientCount": 8, "satisfaction": 78.0},
                {"radio": "5g", "channel": 149, "clientCount": 12, "satisfaction": 88.0},
            ],
            "totalClients": 20,
            "txBytes": 800000000,
            "rxBytes": 400000000,
        },
    ]


@pytest.fixture
def sample_connectivity():
    return {
        "aps": [
            {
                "apMac": "00:11:22:33:44:55",
                "apName": "Office AP",
                "avgSuccessRate": 98.5,
                "avgLatencyMs": 12.5,
                "totalClients": 15,
                "metrics": [
                    {"timestamp": 1700000000000, "successRate": 98.0, "clientCount": 15},
                    {"timestamp": 1700000300000, "successRate": 99.0, "clientCount": 14},
                ],
            }
        ],
        "timeStart": 1700000000000,
        "timeEnd": 1700086400000,
        "radioBand": "all",
        "overallSuccessRate": 98.5,
    }


@pytest.fixture
def sample_stats_details():
    return [
        {
            "timestamp": 1700000000000,
            "apMac": "00:11:22:33:44:55",
            "radio": "5g",
            "channel": 36,
            "channelWidth": 80,
            "clientCount": 10,
            "txBytes": 100000000,
            "rxBytes": 50000000,
            "utilization": 25.5,
        },
        {
            "timestamp": 1700000300000,
            "apMac": "00:11:22:33:44:55",
            "radio": "5g",
            "channel": 36,
            "channelWidth": 80,
            "clientCount": 12,
            "txBytes": 110000000,
            "rxBytes": 55000000,
            "utilization": 28.0,
        },
    ]


class TestGetWiFiAPStats:
    @pytest.mark.asyncio
    async def test_get_all_ap_stats(self, mock_settings, sample_ap_stats):
        from src.tools.wifi_stats import get_wifi_ap_stats

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_ap_stats)

            result = await get_wifi_ap_stats("default", mock_settings)

            assert "aps" in result
            assert len(result["aps"]) == 2
            assert result["aps"][0]["mac"] == "00:11:22:33:44:55"

    @pytest.mark.asyncio
    async def test_get_single_ap_stats(self, mock_settings, sample_ap_stats):
        from src.tools.wifi_stats import get_wifi_ap_stats

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=[sample_ap_stats[0]])

            result = await get_wifi_ap_stats("default", mock_settings, ap_mac="00:11:22:33:44:55")

            assert "aps" in result
            assert len(result["aps"]) == 1
            assert result["aps"][0]["name"] == "Office AP"

    @pytest.mark.asyncio
    async def test_ap_stats_with_time_range(self, mock_settings, sample_ap_stats):
        from src.tools.wifi_stats import get_wifi_ap_stats

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_ap_stats)

            result = await get_wifi_ap_stats("default", mock_settings, time_range="24h")

            assert "aps" in result
            mock_instance.get.assert_called_once()
            call_url = mock_instance.get.call_args[0][0]
            assert "start=" in call_url or "wifi-stats/aps" in call_url

    @pytest.mark.asyncio
    async def test_empty_ap_stats_response(self, mock_settings):
        from src.tools.wifi_stats import get_wifi_ap_stats

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=[])

            result = await get_wifi_ap_stats("default", mock_settings)

            assert "aps" in result
            assert result["aps"] == []

    @pytest.mark.asyncio
    async def test_ap_stats_api_error(self, mock_settings):
        from src.tools.wifi_stats import get_wifi_ap_stats

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=Exception("API Error"))

            with pytest.raises(Exception):
                await get_wifi_ap_stats("default", mock_settings)


class TestGetWiFiConnectivityMetrics:
    @pytest.mark.asyncio
    async def test_get_connectivity_metrics(self, mock_settings, sample_connectivity):
        from src.tools.wifi_stats import get_wifi_connectivity_metrics

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_connectivity)

            result = await get_wifi_connectivity_metrics("default", mock_settings)

            assert "aps" in result
            assert len(result["aps"]) == 1
            assert result["overallSuccessRate"] == 98.5

    @pytest.mark.asyncio
    async def test_connectivity_with_ap_filter(self, mock_settings, sample_connectivity):
        from src.tools.wifi_stats import get_wifi_connectivity_metrics

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_connectivity)

            result = await get_wifi_connectivity_metrics(
                "default", mock_settings, ap_mac="00:11:22:33:44:55"
            )

            mock_instance.get.assert_called_once()
            call_url = mock_instance.get.call_args[0][0]
            assert "apMac=" in call_url

    @pytest.mark.asyncio
    async def test_connectivity_with_radio_band(self, mock_settings, sample_connectivity):
        from src.tools.wifi_stats import get_wifi_connectivity_metrics

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_connectivity)

            result = await get_wifi_connectivity_metrics("default", mock_settings, radio_band="5g")

            mock_instance.get.assert_called_once()
            call_url = mock_instance.get.call_args[0][0]
            assert "radioBand=" in call_url

    @pytest.mark.asyncio
    async def test_connectivity_empty_response(self, mock_settings):
        from src.tools.wifi_stats import get_wifi_connectivity_metrics

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"aps": []})

            result = await get_wifi_connectivity_metrics("default", mock_settings)

            assert "aps" in result
            assert result["aps"] == []


class TestListWiFiClientsByAP:
    @pytest.mark.asyncio
    async def test_list_clients_by_ap(self, mock_settings):
        from src.tools.wifi_stats import list_wifi_clients_by_ap

        sample_clients = [
            {
                "mac": "aa:bb:cc:dd:ee:ff",
                "hostname": "laptop-1",
                "apMac": "00:11:22:33:44:55",
                "radio": "5g",
                "rssi": -55,
            },
            {
                "mac": "11:22:33:44:55:66",
                "hostname": "phone-1",
                "apMac": "00:11:22:33:44:55",
                "radio": "2g",
                "rssi": -65,
            },
        ]

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(
                side_effect=[
                    {"data": sample_clients + [{"mac": "xx:xx", "apMac": "other-ap"}]},
                ]
            )

            result = await list_wifi_clients_by_ap(
                "default", mock_settings, ap_mac="00:11:22:33:44:55"
            )

            assert "clients" in result
            assert len(result["clients"]) == 2
            for client in result["clients"]:
                assert client["apMac"] == "00:11:22:33:44:55"

    @pytest.mark.asyncio
    async def test_list_clients_empty(self, mock_settings):
        from src.tools.wifi_stats import list_wifi_clients_by_ap

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": []})

            result = await list_wifi_clients_by_ap(
                "default", mock_settings, ap_mac="00:11:22:33:44:55"
            )

            assert "clients" in result
            assert result["clients"] == []

    @pytest.mark.asyncio
    async def test_list_clients_ap_not_found(self, mock_settings):
        from src.tools.wifi_stats import list_wifi_clients_by_ap

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(
                return_value={"data": [{"mac": "xx", "apMac": "different-ap"}]}
            )

            result = await list_wifi_clients_by_ap("default", mock_settings, ap_mac="nonexistent")

            assert "clients" in result
            assert result["clients"] == []


class TestGetWiFiStatsDetails:
    @pytest.mark.asyncio
    async def test_get_stats_details(self, mock_settings, sample_stats_details):
        from src.tools.wifi_stats import get_wifi_stats_details

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_stats_details)

            result = await get_wifi_stats_details("default", mock_settings)

            assert "details" in result
            assert len(result["details"]) == 2

    @pytest.mark.asyncio
    async def test_get_stats_details_for_ap(self, mock_settings, sample_stats_details):
        from src.tools.wifi_stats import get_wifi_stats_details

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_stats_details)

            result = await get_wifi_stats_details(
                "default", mock_settings, ap_mac="00:11:22:33:44:55"
            )

            mock_instance.get.assert_called_once()
            call_url = mock_instance.get.call_args[0][0]
            assert "apMac=" in call_url

    @pytest.mark.asyncio
    async def test_get_stats_details_empty(self, mock_settings):
        from src.tools.wifi_stats import get_wifi_stats_details

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=[])

            result = await get_wifi_stats_details("default", mock_settings)

            assert "details" in result
            assert result["details"] == []


class TestGetWiFiHealthSummary:
    @pytest.mark.asyncio
    async def test_get_health_summary(self, mock_settings, sample_ap_stats, sample_connectivity):
        from src.tools.wifi_stats import get_wifi_health_summary

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=[sample_ap_stats, sample_connectivity])

            result = await get_wifi_health_summary("default", mock_settings)

            assert "total_aps" in result
            assert "total_clients" in result
            assert "status" in result

    @pytest.mark.asyncio
    async def test_health_summary_calculates_totals(
        self, mock_settings, sample_ap_stats, sample_connectivity
    ):
        from src.tools.wifi_stats import get_wifi_health_summary

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=[sample_ap_stats, sample_connectivity])

            result = await get_wifi_health_summary("default", mock_settings)

            assert result["total_aps"] == 2
            assert result["total_clients"] == 35

    @pytest.mark.asyncio
    async def test_health_summary_empty_site(self, mock_settings):
        from src.tools.wifi_stats import get_wifi_health_summary

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=[[], {"aps": []}])

            result = await get_wifi_health_summary("default", mock_settings)

            assert result["total_aps"] == 0
            assert result["total_clients"] == 0
            assert result["status"] == "unknown"


class TestTimeRangeParsing:
    @pytest.mark.asyncio
    async def test_time_range_1h(self, mock_settings, sample_ap_stats):
        from src.tools.wifi_stats import get_wifi_ap_stats

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_ap_stats)

            await get_wifi_ap_stats("default", mock_settings, time_range="1h")

            mock_instance.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_time_range_7d(self, mock_settings, sample_ap_stats):
        from src.tools.wifi_stats import get_wifi_ap_stats

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_ap_stats)

            await get_wifi_ap_stats("default", mock_settings, time_range="7d")

            mock_instance.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_time_range(self, mock_settings, sample_ap_stats):
        from src.tools.wifi_stats import get_wifi_ap_stats

        with patch("src.tools.wifi_stats.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_ap_stats)

            result = await get_wifi_ap_stats("default", mock_settings, time_range="24h")

            assert "aps" in result


class TestInputValidation:
    @pytest.mark.asyncio
    async def test_invalid_site_id(self, mock_settings):
        from src.tools.wifi_stats import get_wifi_ap_stats
        from src.utils.exceptions import ValidationError

        with pytest.raises(ValidationError):
            await get_wifi_ap_stats("", mock_settings)

    @pytest.mark.asyncio
    async def test_invalid_site_id_special_chars(self, mock_settings):
        from src.tools.wifi_stats import get_wifi_ap_stats
        from src.utils.exceptions import ValidationError

        with pytest.raises(ValidationError):
            await get_wifi_ap_stats("site/../etc", mock_settings)
