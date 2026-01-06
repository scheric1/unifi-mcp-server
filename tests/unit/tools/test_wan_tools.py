"""Unit tests for WAN load balancing tools.

TDD: Write these tests FIRST, then implement in src/tools/wans.py
Based on API endpoints:
- GET /proxy/network/v2/api/site/{site}/wan/load-balancing/configuration
- GET /proxy/network/v2/api/site/{site}/wan/load-balancing/status
- GET /proxy/network/v2/api/site/{site}/wan/defaults
- GET /proxy/network/v2/api/site/{site}/wan/enriched-configuration
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
def sample_lb_config():
    """Sample load balancing configuration from captured schema."""
    return {
        "mode": "FAILOVER_ONLY",
        "wan_interfaces": [
            {
                "mode": "DISTRIBUTED",
                "name": "Internet 1",
                "priority": 1,
                "wan_networkgroup": "WAN",
                "weight": 50,
            },
            {
                "mode": "FAILOVER_ONLY",
                "name": "Internet 2",
                "priority": 2,
                "wan_networkgroup": "WAN2",
                "weight": 1,
            },
        ],
    }


@pytest.fixture
def sample_lb_status():
    """Sample load balancing status from captured schema."""
    return {
        "wan_interfaces": [
            {"name": "Internet 1", "state": "ACTIVE", "wan_networkgroup": "WAN"},
            {"name": "Internet 2", "state": "BACKUP", "wan_networkgroup": "WAN2"},
        ]
    }


@pytest.fixture
def sample_wan_defaults():
    """Sample WAN defaults from captured schema."""
    return {
        "attr_no_delete": False,
        "purpose": "wan",
        "wan_type": "dhcp",
        "wan_failover_priority": 0,
        "wan_dns_preference": "auto",
        "wan_smartq_enabled": False,
        "wan_provider_capabilities": {
            "download_kilobits_per_second": 0,
            "upload_kilobits_per_second": 0,
        },
    }


@pytest.fixture
def sample_enriched_configs():
    """Sample enriched WAN configurations from captured schema."""
    return [
        {
            "configuration": {
                "_id": "6507f744e35fa70a9663d80c",
                "name": "Internet 1",
                "purpose": "wan",
                "wan_type": "dhcp",
                "wan_networkgroup": "WAN",
                "wan_failover_priority": 1,
                "wan_load_balance_type": "weighted",
                "wan_load_balance_weight": 50,
                "wan_provider_capabilities": {
                    "download_kilobits_per_second": 900000,
                    "upload_kilobits_per_second": 900000,
                },
            },
            "details": {
                "creation_timestamp": 1695020868,
                "service_provider": {"city": "Leominster", "name": "Verizon Fios"},
            },
            "statistics": {
                "peak_usage": {
                    "download_percentage": 12.0,
                    "max_rx_bytes-r": 51533988,
                    "max_tx_bytes-r": 113635175,
                    "upload_percentage": 14.0,
                },
                "uptime_percentage": 100,
            },
        },
        {
            "configuration": {
                "_id": "6507f744e35fa70a9663d80d",
                "name": "Internet 2",
                "purpose": "wan",
                "wan_type": "dhcp",
                "wan_networkgroup": "WAN2",
                "wan_failover_priority": 2,
                "wan_load_balance_type": "failover-only",
                "wan_load_balance_weight": 1,
                "wan_provider_capabilities": {
                    "download_kilobits_per_second": 0,
                    "upload_kilobits_per_second": 0,
                },
            },
            "details": {"creation_timestamp": 1695020868, "service_provider": {}},
            "statistics": {
                "peak_usage": {
                    "download_percentage": -1,
                    "max_rx_bytes-r": 0,
                    "max_tx_bytes-r": 0,
                    "upload_percentage": -1,
                },
                "uptime_percentage": -1,
            },
        },
    ]


class TestGetWANLoadBalancingConfig:
    """Tests for get_wan_load_balancing_config tool."""

    @pytest.mark.asyncio
    async def test_get_config_success(self, mock_settings, sample_lb_config):
        """Get load balancing configuration successfully."""
        from src.tools.wans import get_wan_load_balancing_config

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=sample_lb_config)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await get_wan_load_balancing_config("default", mock_settings)

            assert result["mode"] == "FAILOVER_ONLY"
            assert len(result["wan_interfaces"]) == 2

    @pytest.mark.asyncio
    async def test_get_config_failover_mode(self, mock_settings, sample_lb_config):
        """Get configuration in failover-only mode."""
        from src.tools.wans import get_wan_load_balancing_config

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=sample_lb_config)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await get_wan_load_balancing_config("default", mock_settings)

            assert result["mode"] == "FAILOVER_ONLY"
            assert result["wan_interfaces"][1]["mode"] == "FAILOVER_ONLY"

    @pytest.mark.asyncio
    async def test_get_config_distributed_mode(self, mock_settings):
        """Get configuration in distributed mode."""
        from src.tools.wans import get_wan_load_balancing_config

        distributed_config = {
            "mode": "DISTRIBUTED",
            "wan_interfaces": [
                {
                    "mode": "DISTRIBUTED",
                    "name": "Internet 1",
                    "priority": 1,
                    "wan_networkgroup": "WAN",
                    "weight": 50,
                },
                {
                    "mode": "DISTRIBUTED",
                    "name": "Internet 2",
                    "priority": 2,
                    "wan_networkgroup": "WAN2",
                    "weight": 50,
                },
            ],
        }

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=distributed_config)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await get_wan_load_balancing_config("default", mock_settings)

            assert result["mode"] == "DISTRIBUTED"
            assert all(iface["mode"] == "DISTRIBUTED" for iface in result["wan_interfaces"])

    @pytest.mark.asyncio
    async def test_get_config_dual_wan_priorities(self, mock_settings, sample_lb_config):
        """Verify dual-WAN priority configuration."""
        from src.tools.wans import get_wan_load_balancing_config

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=sample_lb_config)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await get_wan_load_balancing_config("default", mock_settings)

            assert result["wan_interfaces"][0]["priority"] == 1
            assert result["wan_interfaces"][1]["priority"] == 2

    @pytest.mark.asyncio
    async def test_get_config_authenticates_if_needed(self, mock_settings, sample_lb_config):
        """Tool authenticates if not already authenticated."""
        from src.tools.wans import get_wan_load_balancing_config

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = False
            mock_client.authenticate = AsyncMock()
            mock_client.get = AsyncMock(return_value=sample_lb_config)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await get_wan_load_balancing_config("default", mock_settings)

            mock_client.authenticate.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_config_correct_endpoint(self, mock_settings, sample_lb_config):
        """Tool calls correct API endpoint."""
        from src.tools.wans import get_wan_load_balancing_config

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=sample_lb_config)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await get_wan_load_balancing_config("my-site", mock_settings)

            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args[0][0]
            assert "my-site" in call_args
            assert "load-balancing/configuration" in call_args


class TestGetWANLoadBalancingStatus:
    """Tests for get_wan_load_balancing_status tool."""

    @pytest.mark.asyncio
    async def test_get_status_success(self, mock_settings, sample_lb_status):
        """Get load balancing status successfully."""
        from src.tools.wans import get_wan_load_balancing_status

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=sample_lb_status)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await get_wan_load_balancing_status("default", mock_settings)

            assert len(result["wan_interfaces"]) == 2

    @pytest.mark.asyncio
    async def test_get_status_normal_operation(self, mock_settings, sample_lb_status):
        """Get status when primary WAN is active."""
        from src.tools.wans import get_wan_load_balancing_status

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=sample_lb_status)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await get_wan_load_balancing_status("default", mock_settings)

            assert result["wan_interfaces"][0]["state"] == "ACTIVE"
            assert result["wan_interfaces"][1]["state"] == "BACKUP"

    @pytest.mark.asyncio
    async def test_get_status_failover_active(self, mock_settings):
        """Get status during failover to backup WAN."""
        from src.tools.wans import get_wan_load_balancing_status

        failover_status = {
            "wan_interfaces": [
                {"name": "Internet 1", "state": "DISCONNECTED", "wan_networkgroup": "WAN"},
                {"name": "Internet 2", "state": "ACTIVE", "wan_networkgroup": "WAN2"},
            ]
        }

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=failover_status)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await get_wan_load_balancing_status("default", mock_settings)

            assert result["wan_interfaces"][0]["state"] == "DISCONNECTED"
            assert result["wan_interfaces"][1]["state"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_get_status_all_disconnected(self, mock_settings):
        """Handle case where all WANs are disconnected."""
        from src.tools.wans import get_wan_load_balancing_status

        disconnected_status = {
            "wan_interfaces": [
                {"name": "Internet 1", "state": "DISCONNECTED", "wan_networkgroup": "WAN"},
                {"name": "Internet 2", "state": "DISCONNECTED", "wan_networkgroup": "WAN2"},
            ]
        }

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=disconnected_status)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await get_wan_load_balancing_status("default", mock_settings)

            assert all(iface["state"] == "DISCONNECTED" for iface in result["wan_interfaces"])

    @pytest.mark.asyncio
    async def test_get_status_correct_endpoint(self, mock_settings, sample_lb_status):
        """Tool calls correct API endpoint."""
        from src.tools.wans import get_wan_load_balancing_status

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=sample_lb_status)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await get_wan_load_balancing_status("my-site", mock_settings)

            call_args = mock_client.get.call_args[0][0]
            assert "my-site" in call_args
            assert "load-balancing/status" in call_args


class TestGetWANDefaults:
    """Tests for get_wan_defaults tool."""

    @pytest.mark.asyncio
    async def test_get_defaults_success(self, mock_settings, sample_wan_defaults):
        """Get WAN defaults successfully."""
        from src.tools.wans import get_wan_defaults

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=sample_wan_defaults)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await get_wan_defaults("default", mock_settings)

            assert result["purpose"] == "wan"
            assert result["wan_type"] == "dhcp"

    @pytest.mark.asyncio
    async def test_get_defaults_has_provider_capabilities(self, mock_settings, sample_wan_defaults):
        """Defaults include provider capabilities."""
        from src.tools.wans import get_wan_defaults

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=sample_wan_defaults)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await get_wan_defaults("default", mock_settings)

            assert "wan_provider_capabilities" in result
            assert result["wan_provider_capabilities"]["download_kilobits_per_second"] == 0

    @pytest.mark.asyncio
    async def test_get_defaults_correct_endpoint(self, mock_settings, sample_wan_defaults):
        """Tool calls correct API endpoint."""
        from src.tools.wans import get_wan_defaults

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=sample_wan_defaults)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await get_wan_defaults("my-site", mock_settings)

            call_args = mock_client.get.call_args[0][0]
            assert "my-site" in call_args
            assert "wan/defaults" in call_args


class TestGetWANEnrichedConfiguration:
    """Tests for get_wan_enriched_configuration tool."""

    @pytest.mark.asyncio
    async def test_get_enriched_success(self, mock_settings, sample_enriched_configs):
        """Get enriched WAN configurations successfully."""
        from src.tools.wans import get_wan_enriched_configuration

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=sample_enriched_configs)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await get_wan_enriched_configuration("default", mock_settings)

            assert len(result) == 2
            assert result[0]["configuration"]["name"] == "Internet 1"

    @pytest.mark.asyncio
    async def test_get_enriched_includes_statistics(self, mock_settings, sample_enriched_configs):
        """Enriched config includes statistics."""
        from src.tools.wans import get_wan_enriched_configuration

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=sample_enriched_configs)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await get_wan_enriched_configuration("default", mock_settings)

            assert "statistics" in result[0]
            assert result[0]["statistics"]["uptime_percentage"] == 100

    @pytest.mark.asyncio
    async def test_get_enriched_includes_service_provider(
        self, mock_settings, sample_enriched_configs
    ):
        """Enriched config includes service provider info."""
        from src.tools.wans import get_wan_enriched_configuration

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=sample_enriched_configs)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await get_wan_enriched_configuration("default", mock_settings)

            assert result[0]["details"]["service_provider"]["name"] == "Verizon Fios"

    @pytest.mark.asyncio
    async def test_get_enriched_handles_empty_provider(
        self, mock_settings, sample_enriched_configs
    ):
        """Enriched config handles empty service provider."""
        from src.tools.wans import get_wan_enriched_configuration

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=sample_enriched_configs)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await get_wan_enriched_configuration("default", mock_settings)

            assert result[1]["details"]["service_provider"]["name"] is None
            assert result[1]["details"]["service_provider"]["city"] is None

    @pytest.mark.asyncio
    async def test_get_enriched_correct_endpoint(self, mock_settings, sample_enriched_configs):
        """Tool calls correct API endpoint."""
        from src.tools.wans import get_wan_enriched_configuration

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=sample_enriched_configs)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await get_wan_enriched_configuration("my-site", mock_settings)

            call_args = mock_client.get.call_args[0][0]
            assert "my-site" in call_args
            assert "enriched-configuration" in call_args


class TestListWANConnections:
    """Tests for list_wan_connections tool (existing, verify it still works)."""

    @pytest.mark.asyncio
    async def test_list_connections_single_wan(self, mock_settings):
        """List connections for single-WAN setup."""
        from src.tools.wans import list_wan_connections

        single_wan = {
            "data": [
                {
                    "_id": "wan1",
                    "site_id": "default",
                    "name": "Internet 1",
                    "wan_type": "dhcp",
                    "interface": "eth0",
                    "status": "online",
                }
            ]
        }

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=single_wan)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await list_wan_connections("default", mock_settings)

            assert len(result) == 1
            assert result[0]["name"] == "Internet 1"

    @pytest.mark.asyncio
    async def test_list_connections_dual_wan(self, mock_settings):
        """List connections for dual-WAN setup."""
        from src.tools.wans import list_wan_connections

        dual_wan = {
            "data": [
                {
                    "_id": "wan1",
                    "site_id": "default",
                    "name": "Internet 1",
                    "wan_type": "dhcp",
                    "interface": "eth0",
                    "status": "online",
                },
                {
                    "_id": "wan2",
                    "site_id": "default",
                    "name": "Internet 2",
                    "wan_type": "dhcp",
                    "interface": "eth1",
                    "status": "offline",
                },
            ]
        }

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=dual_wan)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await list_wan_connections("default", mock_settings)

            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_connections_empty(self, mock_settings):
        """Handle empty WAN list gracefully."""
        from src.tools.wans import list_wan_connections

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value={"data": []})
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await list_wan_connections("default", mock_settings)

            assert result == []


class TestGetWANFailoverHistory:
    """Tests for get_wan_failover_history tool."""

    @pytest.mark.asyncio
    async def test_get_failover_history_success(self, mock_settings):
        """Get failover history successfully."""
        from src.tools.wans import get_wan_failover_history

        history_data = [
            {
                "timestamp": 1767566897127,
                "event": "FAILOVER",
                "from_wan": "Internet 1",
                "to_wan": "Internet 2",
                "reason": "PRIMARY_DISCONNECTED",
            },
            {
                "timestamp": 1767566997127,
                "event": "FAILBACK",
                "from_wan": "Internet 2",
                "to_wan": "Internet 1",
                "reason": "PRIMARY_RESTORED",
            },
        ]

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=history_data)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await get_wan_failover_history("default", mock_settings)

            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_failover_history_with_limit(self, mock_settings):
        """Get failover history with limit parameter."""
        from src.tools.wans import get_wan_failover_history

        history_data = [
            {
                "timestamp": 1767566897127,
                "event": "FAILOVER",
                "from_wan": "Internet 1",
                "to_wan": "Internet 2",
                "reason": "PRIMARY_DISCONNECTED",
            }
        ]

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=history_data)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await get_wan_failover_history("default", mock_settings, limit=10)

            assert len(result) <= 10

    @pytest.mark.asyncio
    async def test_get_failover_history_empty(self, mock_settings):
        """Handle empty failover history."""
        from src.tools.wans import get_wan_failover_history

        with patch("src.tools.wans.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_authenticated = True
            mock_client.get = AsyncMock(return_value=[])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await get_wan_failover_history("default", mock_settings)

            assert result == []
