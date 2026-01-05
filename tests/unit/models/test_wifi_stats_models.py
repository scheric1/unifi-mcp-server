"""Unit tests for WiFi statistics and connectivity models.

TDD: Write these tests FIRST, then implement in src/models/wifi_stats.py
Based on endpoints:
- /proxy/network/v2/api/site/{site}/wifi-stats/aps
- /proxy/network/v2/api/site/{site}/wifi-connectivity
- /proxy/network/v2/api/site/{site}/wifi-stats/details
"""

import pytest
from pydantic import ValidationError


class TestRadioBand:
    """Tests for RadioBand enum."""

    def test_band_2g_value(self):
        from src.models.wifi_stats import RadioBand

        assert RadioBand.BAND_2G.value == "2g"

    def test_band_5g_value(self):
        from src.models.wifi_stats import RadioBand

        assert RadioBand.BAND_5G.value == "5g"

    def test_band_6g_value(self):
        from src.models.wifi_stats import RadioBand

        assert RadioBand.BAND_6G.value == "6g"

    def test_all_value(self):
        from src.models.wifi_stats import RadioBand

        assert RadioBand.ALL.value == "all"

    def test_invalid_band_raises(self):
        from src.models.wifi_stats import RadioBand

        with pytest.raises(ValueError):
            RadioBand("invalid")


class TestConnectivityStatus:
    """Tests for ConnectivityStatus enum."""

    def test_excellent_value(self):
        from src.models.wifi_stats import ConnectivityStatus

        assert ConnectivityStatus.EXCELLENT.value == "excellent"

    def test_good_value(self):
        from src.models.wifi_stats import ConnectivityStatus

        assert ConnectivityStatus.GOOD.value == "good"

    def test_fair_value(self):
        from src.models.wifi_stats import ConnectivityStatus

        assert ConnectivityStatus.FAIR.value == "fair"

    def test_poor_value(self):
        from src.models.wifi_stats import ConnectivityStatus

        assert ConnectivityStatus.POOR.value == "poor"

    def test_unknown_value(self):
        from src.models.wifi_stats import ConnectivityStatus

        assert ConnectivityStatus.UNKNOWN.value == "unknown"


class TestAPRadioStats:
    """Tests for APRadioStats model."""

    def test_parse_minimal(self):
        from src.models.wifi_stats import APRadioStats

        data = {"radio": "5g"}
        stats = APRadioStats(**data)
        assert stats.radio == "5g"
        assert stats.client_count == 0

    def test_parse_full(self):
        from src.models.wifi_stats import APRadioStats

        data = {
            "radio": "5g",
            "channel": 36,
            "channelWidth": 80,
            "txPower": 20,
            "noiseFloor": -90,
            "utilization": 25.5,
            "clientCount": 15,
            "satisfaction": 92.5,
        }
        stats = APRadioStats(**data)

        assert stats.radio == "5g"
        assert stats.channel == 36
        assert stats.channel_width == 80
        assert stats.tx_power == 20
        assert stats.noise_floor == -90
        assert stats.utilization == 25.5
        assert stats.client_count == 15
        assert stats.satisfaction == 92.5

    def test_alias_field_access(self):
        from src.models.wifi_stats import APRadioStats

        data = {"radio": "2g", "clientCount": 10}
        stats = APRadioStats(**data)
        assert stats.client_count == 10

    def test_allows_extra_fields(self):
        from src.models.wifi_stats import APRadioStats

        data = {"radio": "5g", "unknownField": "value"}
        stats = APRadioStats(**data)
        assert stats.radio == "5g"


class TestAPStats:
    """Tests for APStats model."""

    def test_parse_minimal(self):
        from src.models.wifi_stats import APStats

        data = {"mac": "00:11:22:33:44:55"}
        stats = APStats(**data)

        assert stats.mac == "00:11:22:33:44:55"
        assert stats.total_clients == 0
        assert stats.radios == []

    def test_parse_full(self):
        from src.models.wifi_stats import APStats

        data = {
            "mac": "00:11:22:33:44:55",
            "name": "Office AP",
            "model": "U7-Pro",
            "radios": [
                {"radio": "2g", "clientCount": 5},
                {"radio": "5g", "clientCount": 10},
            ],
            "totalClients": 15,
            "txBytes": 1000000,
            "rxBytes": 500000,
            "txPackets": 1000,
            "rxPackets": 500,
            "txRetries": 50,
            "uptime": 86400,
        }
        stats = APStats(**data)

        assert stats.mac == "00:11:22:33:44:55"
        assert stats.name == "Office AP"
        assert stats.model == "U7-Pro"
        assert len(stats.radios) == 2
        assert stats.total_clients == 15
        assert stats.tx_bytes == 1000000
        assert stats.rx_bytes == 500000
        assert stats.uptime == 86400

    def test_radios_are_parsed_correctly(self):
        from src.models.wifi_stats import APStats

        data = {
            "mac": "00:11:22:33:44:55",
            "radios": [{"radio": "5g", "channel": 36, "clientCount": 10}],
        }
        stats = APStats(**data)

        assert len(stats.radios) == 1
        assert stats.radios[0].radio == "5g"
        assert stats.radios[0].channel == 36
        assert stats.radios[0].client_count == 10


class TestWiFiAPStatsResponse:
    """Tests for WiFiAPStatsResponse model."""

    def test_parse_empty_response(self):
        from src.models.wifi_stats import WiFiAPStatsResponse

        data = {"aps": []}
        response = WiFiAPStatsResponse(**data)

        assert response.aps == []
        assert response.time_start is None

    def test_parse_with_aps(self):
        from src.models.wifi_stats import WiFiAPStatsResponse

        data = {
            "aps": [
                {"mac": "00:11:22:33:44:55", "name": "AP1"},
                {"mac": "66:77:88:99:aa:bb", "name": "AP2"},
            ],
            "timeStart": 1700000000000,
            "timeEnd": 1700086400000,
        }
        response = WiFiAPStatsResponse(**data)

        assert len(response.aps) == 2
        assert response.aps[0].mac == "00:11:22:33:44:55"
        assert response.time_start == 1700000000000
        assert response.time_end == 1700086400000


class TestWiFiClientStats:
    """Tests for WiFiClientStats model."""

    def test_parse_minimal(self):
        from src.models.wifi_stats import WiFiClientStats

        data = {"mac": "aa:bb:cc:dd:ee:ff"}
        stats = WiFiClientStats(**data)

        assert stats.mac == "aa:bb:cc:dd:ee:ff"
        assert stats.tx_bytes == 0
        assert stats.rx_bytes == 0

    def test_parse_full(self):
        from src.models.wifi_stats import WiFiClientStats

        data = {
            "mac": "aa:bb:cc:dd:ee:ff",
            "hostname": "laptop-user",
            "ip": "192.168.1.100",
            "apMac": "00:11:22:33:44:55",
            "radio": "5g",
            "channel": 36,
            "rssi": -55,
            "noise": -90,
            "snr": 35,
            "txRate": 866000,
            "rxRate": 433000,
            "txBytes": 1000000,
            "rxBytes": 500000,
            "satisfaction": 95.0,
            "uptime": 3600,
        }
        stats = WiFiClientStats(**data)

        assert stats.hostname == "laptop-user"
        assert stats.ip == "192.168.1.100"
        assert stats.ap_mac == "00:11:22:33:44:55"
        assert stats.rssi == -55
        assert stats.snr == 35
        assert stats.tx_rate == 866000
        assert stats.satisfaction == 95.0


class TestConnectivityMetric:
    """Tests for ConnectivityMetric model."""

    def test_parse_minimal(self):
        from src.models.wifi_stats import ConnectivityMetric

        data = {"timestamp": 1700000000000}
        metric = ConnectivityMetric(**data)

        assert metric.timestamp == 1700000000000
        assert metric.success_rate == 0
        assert metric.client_count == 0

    def test_parse_full(self):
        from src.models.wifi_stats import ConnectivityMetric

        data = {
            "timestamp": 1700000000000,
            "successRate": 98.5,
            "latencyMs": 15.2,
            "clientCount": 25,
            "satisfaction": 92.0,
        }
        metric = ConnectivityMetric(**data)

        assert metric.success_rate == 98.5
        assert metric.latency_ms == 15.2
        assert metric.client_count == 25
        assert metric.satisfaction == 92.0


class TestAPConnectivity:
    """Tests for APConnectivity model."""

    def test_parse_minimal(self):
        from src.models.wifi_stats import APConnectivity

        data = {"apMac": "00:11:22:33:44:55"}
        ap = APConnectivity(**data)

        assert ap.ap_mac == "00:11:22:33:44:55"
        assert ap.metrics == []
        assert ap.avg_success_rate == 0

    def test_parse_full(self):
        from src.models.wifi_stats import APConnectivity

        data = {
            "apMac": "00:11:22:33:44:55",
            "apName": "Office AP",
            "metrics": [
                {"timestamp": 1700000000000, "successRate": 98.0},
                {"timestamp": 1700000300000, "successRate": 99.0},
            ],
            "avgSuccessRate": 98.5,
            "avgLatencyMs": 12.5,
            "totalClients": 30,
        }
        ap = APConnectivity(**data)

        assert ap.ap_name == "Office AP"
        assert len(ap.metrics) == 2
        assert ap.avg_success_rate == 98.5
        assert ap.avg_latency_ms == 12.5
        assert ap.total_clients == 30


class TestWiFiConnectivityResponse:
    """Tests for WiFiConnectivityResponse model."""

    def test_parse_empty(self):
        from src.models.wifi_stats import WiFiConnectivityResponse

        data = {"aps": []}
        response = WiFiConnectivityResponse(**data)

        assert response.aps == []
        assert response.overall_success_rate == 0

    def test_parse_full(self):
        from src.models.wifi_stats import WiFiConnectivityResponse

        data = {
            "aps": [{"apMac": "00:11:22:33:44:55", "avgSuccessRate": 98.0}],
            "timeStart": 1700000000000,
            "timeEnd": 1700086400000,
            "radioBand": "all",
            "overallSuccessRate": 98.0,
        }
        response = WiFiConnectivityResponse(**data)

        assert len(response.aps) == 1
        assert response.radio_band == "all"
        assert response.overall_success_rate == 98.0


class TestWiFiStatsDetail:
    """Tests for WiFiStatsDetail model."""

    def test_parse_minimal(self):
        from src.models.wifi_stats import WiFiStatsDetail

        data = {"timestamp": 1700000000000, "apMac": "00:11:22:33:44:55"}
        detail = WiFiStatsDetail(**data)

        assert detail.timestamp == 1700000000000
        assert detail.ap_mac == "00:11:22:33:44:55"
        assert detail.client_count == 0

    def test_parse_full(self):
        from src.models.wifi_stats import WiFiStatsDetail

        data = {
            "timestamp": 1700000000000,
            "apMac": "00:11:22:33:44:55",
            "radio": "5g",
            "channel": 36,
            "channelWidth": 80,
            "clientCount": 10,
            "txBytes": 1000000,
            "rxBytes": 500000,
            "txRetries": 50,
            "utilization": 25.5,
            "interference": 5.0,
        }
        detail = WiFiStatsDetail(**data)

        assert detail.radio == "5g"
        assert detail.channel == 36
        assert detail.channel_width == 80
        assert detail.utilization == 25.5
        assert detail.interference == 5.0


class TestWiFiStatsDetailsResponse:
    """Tests for WiFiStatsDetailsResponse model."""

    def test_parse_empty(self):
        from src.models.wifi_stats import WiFiStatsDetailsResponse

        data = {"details": []}
        response = WiFiStatsDetailsResponse(**data)

        assert response.details == []

    def test_parse_full(self):
        from src.models.wifi_stats import WiFiStatsDetailsResponse

        data = {
            "details": [
                {"timestamp": 1700000000000, "apMac": "00:11:22:33:44:55"},
                {"timestamp": 1700000300000, "apMac": "00:11:22:33:44:55"},
            ],
            "timeStart": 1700000000000,
            "timeEnd": 1700086400000,
            "apMac": "00:11:22:33:44:55",
        }
        response = WiFiStatsDetailsResponse(**data)

        assert len(response.details) == 2
        assert response.ap_mac == "00:11:22:33:44:55"


class TestWiFiHealthSummary:
    """Tests for WiFiHealthSummary model."""

    def test_parse_minimal(self):
        from src.models.wifi_stats import WiFiHealthSummary

        data = {}
        summary = WiFiHealthSummary(**data)

        assert summary.total_aps == 0
        assert summary.total_clients == 0

    def test_parse_full(self):
        from src.models.wifi_stats import WiFiHealthSummary

        data = {
            "totalAPs": 5,
            "onlineAPs": 5,
            "totalClients": 50,
            "avgSatisfaction": 92.5,
            "avgSuccessRate": 98.0,
            "clients2g": 10,
            "clients5g": 35,
            "clients6g": 5,
        }
        summary = WiFiHealthSummary(**data)

        assert summary.total_aps == 5
        assert summary.online_aps == 5
        assert summary.total_clients == 50
        assert summary.avg_satisfaction == 92.5
        assert summary.clients_2g == 10
        assert summary.clients_5g == 35
        assert summary.clients_6g == 5

    def test_status_excellent(self):
        from src.models.wifi_stats import ConnectivityStatus, WiFiHealthSummary

        summary = WiFiHealthSummary(avgSatisfaction=95.0)
        assert summary.status == ConnectivityStatus.EXCELLENT

    def test_status_good(self):
        from src.models.wifi_stats import ConnectivityStatus, WiFiHealthSummary

        summary = WiFiHealthSummary(avgSatisfaction=80.0)
        assert summary.status == ConnectivityStatus.GOOD

    def test_status_fair(self):
        from src.models.wifi_stats import ConnectivityStatus, WiFiHealthSummary

        summary = WiFiHealthSummary(avgSatisfaction=60.0)
        assert summary.status == ConnectivityStatus.FAIR

    def test_status_poor(self):
        from src.models.wifi_stats import ConnectivityStatus, WiFiHealthSummary

        summary = WiFiHealthSummary(avgSatisfaction=30.0)
        assert summary.status == ConnectivityStatus.POOR

    def test_status_unknown_when_no_satisfaction(self):
        from src.models.wifi_stats import ConnectivityStatus, WiFiHealthSummary

        summary = WiFiHealthSummary()
        assert summary.status == ConnectivityStatus.UNKNOWN


class TestModelConfigConsistency:
    """Tests for consistent model configuration."""

    def test_all_models_allow_extra(self):
        from src.models.wifi_stats import (
            APConnectivity,
            APRadioStats,
            APStats,
            ConnectivityMetric,
            WiFiAPStatsResponse,
            WiFiClientStats,
            WiFiConnectivityResponse,
            WiFiHealthSummary,
            WiFiStatsDetail,
            WiFiStatsDetailsResponse,
        )

        models = [
            APRadioStats,
            APStats,
            WiFiAPStatsResponse,
            WiFiClientStats,
            ConnectivityMetric,
            APConnectivity,
            WiFiConnectivityResponse,
            WiFiStatsDetail,
            WiFiStatsDetailsResponse,
            WiFiHealthSummary,
        ]

        for model in models:
            config = model.model_config
            assert config.get("extra") == "allow", f"{model.__name__} should allow extra fields"
            assert config.get("populate_by_name") is True, (
                f"{model.__name__} should populate_by_name"
            )
