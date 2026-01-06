"""Unit tests for WAN load balancing models.

TDD: Write these tests FIRST, then implement in src/models/wan.py
Based on captured schemas in docs/research/schemas/wan-*.json
"""

import pytest
from pydantic import ValidationError


class TestWANLoadBalancingMode:
    """Tests for WANLoadBalancingMode enum."""

    def test_failover_only_value(self):
        """FAILOVER_ONLY should be a valid mode."""
        from src.models.wan import WANLoadBalancingMode

        assert WANLoadBalancingMode.FAILOVER_ONLY.value == "FAILOVER_ONLY"

    def test_distributed_value(self):
        """DISTRIBUTED should be a valid mode."""
        from src.models.wan import WANLoadBalancingMode

        assert WANLoadBalancingMode.DISTRIBUTED.value == "DISTRIBUTED"

    def test_weighted_load_balance_value(self):
        """WEIGHTED_LOAD_BALANCE should be a valid mode."""
        from src.models.wan import WANLoadBalancingMode

        assert WANLoadBalancingMode.WEIGHTED_LOAD_BALANCE.value == "WEIGHTED_LOAD_BALANCE"

    def test_invalid_mode_raises(self):
        """Invalid mode should raise ValueError."""
        from src.models.wan import WANLoadBalancingMode

        with pytest.raises(ValueError):
            WANLoadBalancingMode("INVALID_MODE")


class TestWANInterfaceState:
    """Tests for WANInterfaceState enum."""

    def test_active_value(self):
        """ACTIVE should be a valid state."""
        from src.models.wan import WANInterfaceState

        assert WANInterfaceState.ACTIVE.value == "ACTIVE"

    def test_backup_value(self):
        """BACKUP should be a valid state."""
        from src.models.wan import WANInterfaceState

        assert WANInterfaceState.BACKUP.value == "BACKUP"

    def test_disconnected_value(self):
        """DISCONNECTED should be a valid state."""
        from src.models.wan import WANInterfaceState

        assert WANInterfaceState.DISCONNECTED.value == "DISCONNECTED"

    def test_connecting_value(self):
        """CONNECTING should be a valid state."""
        from src.models.wan import WANInterfaceState

        assert WANInterfaceState.CONNECTING.value == "CONNECTING"


class TestWANInterfaceMode:
    """Tests for WANInterfaceMode enum."""

    def test_distributed_value(self):
        """DISTRIBUTED should be a valid interface mode."""
        from src.models.wan import WANInterfaceMode

        assert WANInterfaceMode.DISTRIBUTED.value == "DISTRIBUTED"

    def test_failover_only_value(self):
        """FAILOVER_ONLY should be a valid interface mode."""
        from src.models.wan import WANInterfaceMode

        assert WANInterfaceMode.FAILOVER_ONLY.value == "FAILOVER_ONLY"


class TestWANInterface:
    """Tests for WANInterface model."""

    def test_parse_primary_interface(self):
        """Parse primary WAN interface from captured schema."""
        from src.models.wan import WANInterface

        data = {
            "mode": "DISTRIBUTED",
            "name": "Internet 1",
            "priority": 1,
            "wan_networkgroup": "WAN",
            "weight": 50,
        }
        interface = WANInterface(**data)

        assert interface.name == "Internet 1"
        assert interface.mode == "DISTRIBUTED"
        assert interface.priority == 1
        assert interface.wan_networkgroup == "WAN"
        assert interface.weight == 50

    def test_parse_backup_interface(self):
        """Parse backup WAN interface from captured schema."""
        from src.models.wan import WANInterface

        data = {
            "mode": "FAILOVER_ONLY",
            "name": "Internet 2",
            "priority": 2,
            "wan_networkgroup": "WAN2",
            "weight": 1,
        }
        interface = WANInterface(**data)

        assert interface.name == "Internet 2"
        assert interface.mode == "FAILOVER_ONLY"
        assert interface.priority == 2
        assert interface.wan_networkgroup == "WAN2"
        assert interface.weight == 1

    def test_required_fields(self):
        """All required fields must be provided."""
        from src.models.wan import WANInterface

        with pytest.raises(ValidationError):
            WANInterface(name="Test")  # Missing mode, priority, wan_networkgroup, weight

    def test_priority_validation(self):
        """Priority must be positive integer."""
        from src.models.wan import WANInterface

        data = {
            "mode": "DISTRIBUTED",
            "name": "Internet 1",
            "priority": 0,  # Edge case: 0 should be valid
            "wan_networkgroup": "WAN",
            "weight": 50,
        }
        interface = WANInterface(**data)
        assert interface.priority == 0

    def test_weight_validation(self):
        """Weight must be between 1 and 100."""
        from src.models.wan import WANInterface

        data = {
            "mode": "DISTRIBUTED",
            "name": "Internet 1",
            "priority": 1,
            "wan_networkgroup": "WAN",
            "weight": 100,  # Max weight
        }
        interface = WANInterface(**data)
        assert interface.weight == 100


class TestWANInterfaceStatus:
    """Tests for WANInterfaceStatus model."""

    def test_parse_active_status(self):
        """Parse active WAN interface status from captured schema."""
        from src.models.wan import WANInterfaceStatus

        data = {"name": "Internet 1", "state": "ACTIVE", "wan_networkgroup": "WAN"}
        status = WANInterfaceStatus(**data)

        assert status.name == "Internet 1"
        assert status.state == "ACTIVE"
        assert status.wan_networkgroup == "WAN"

    def test_parse_backup_status(self):
        """Parse backup WAN interface status from captured schema."""
        from src.models.wan import WANInterfaceStatus

        data = {"name": "Internet 2", "state": "BACKUP", "wan_networkgroup": "WAN2"}
        status = WANInterfaceStatus(**data)

        assert status.name == "Internet 2"
        assert status.state == "BACKUP"
        assert status.wan_networkgroup == "WAN2"

    def test_disconnected_state(self):
        """Parse disconnected WAN interface status."""
        from src.models.wan import WANInterfaceStatus

        data = {"name": "Internet 2", "state": "DISCONNECTED", "wan_networkgroup": "WAN2"}
        status = WANInterfaceStatus(**data)
        assert status.state == "DISCONNECTED"

    def test_connecting_state(self):
        """Parse connecting WAN interface status."""
        from src.models.wan import WANInterfaceStatus

        data = {"name": "Internet 2", "state": "CONNECTING", "wan_networkgroup": "WAN2"}
        status = WANInterfaceStatus(**data)
        assert status.state == "CONNECTING"


class TestWANLoadBalancingConfig:
    """Tests for WANLoadBalancingConfig model."""

    def test_parse_failover_config(self):
        """Parse failover-only configuration from captured schema."""
        from src.models.wan import WANLoadBalancingConfig

        data = {
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
        config = WANLoadBalancingConfig(**data)

        assert config.mode == "FAILOVER_ONLY"
        assert len(config.wan_interfaces) == 2
        assert config.wan_interfaces[0].name == "Internet 1"
        assert config.wan_interfaces[1].name == "Internet 2"

    def test_parse_distributed_mode(self):
        """Parse distributed/weighted load balancing config."""
        from src.models.wan import WANLoadBalancingConfig

        data = {
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
        config = WANLoadBalancingConfig(**data)

        assert config.mode == "DISTRIBUTED"
        assert all(iface.mode == "DISTRIBUTED" for iface in config.wan_interfaces)

    def test_interface_priorities(self):
        """Verify priority ordering is correct."""
        from src.models.wan import WANLoadBalancingConfig

        data = {
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
        config = WANLoadBalancingConfig(**data)

        # Primary WAN should have lower priority number
        assert config.wan_interfaces[0].priority < config.wan_interfaces[1].priority

    def test_empty_interfaces_list(self):
        """Config with empty interfaces list should be valid."""
        from src.models.wan import WANLoadBalancingConfig

        data = {"mode": "FAILOVER_ONLY", "wan_interfaces": []}
        config = WANLoadBalancingConfig(**data)
        assert config.wan_interfaces == []

    def test_model_dump(self):
        """Model should serialize correctly."""
        from src.models.wan import WANLoadBalancingConfig

        data = {
            "mode": "FAILOVER_ONLY",
            "wan_interfaces": [
                {
                    "mode": "DISTRIBUTED",
                    "name": "Internet 1",
                    "priority": 1,
                    "wan_networkgroup": "WAN",
                    "weight": 50,
                }
            ],
        }
        config = WANLoadBalancingConfig(**data)
        dumped = config.model_dump()

        assert dumped["mode"] == "FAILOVER_ONLY"
        assert len(dumped["wan_interfaces"]) == 1


class TestWANLoadBalancingStatus:
    """Tests for WANLoadBalancingStatus model."""

    def test_parse_status_active_backup(self):
        """Parse status with primary active, secondary backup."""
        from src.models.wan import WANLoadBalancingStatus

        data = {
            "wan_interfaces": [
                {"name": "Internet 1", "state": "ACTIVE", "wan_networkgroup": "WAN"},
                {"name": "Internet 2", "state": "BACKUP", "wan_networkgroup": "WAN2"},
            ]
        }
        status = WANLoadBalancingStatus(**data)

        assert len(status.wan_interfaces) == 2
        assert status.wan_interfaces[0].state == "ACTIVE"
        assert status.wan_interfaces[1].state == "BACKUP"

    def test_detect_failover_state(self):
        """Detect when failover has occurred (backup becomes active)."""
        from src.models.wan import WANLoadBalancingStatus

        data = {
            "wan_interfaces": [
                {"name": "Internet 1", "state": "DISCONNECTED", "wan_networkgroup": "WAN"},
                {"name": "Internet 2", "state": "ACTIVE", "wan_networkgroup": "WAN2"},
            ]
        }
        status = WANLoadBalancingStatus(**data)

        # Primary is disconnected, backup is active = failover occurred
        assert status.wan_interfaces[0].state == "DISCONNECTED"
        assert status.wan_interfaces[1].state == "ACTIVE"

    def test_all_disconnected(self):
        """Handle case where all WANs are disconnected."""
        from src.models.wan import WANLoadBalancingStatus

        data = {
            "wan_interfaces": [
                {"name": "Internet 1", "state": "DISCONNECTED", "wan_networkgroup": "WAN"},
                {"name": "Internet 2", "state": "DISCONNECTED", "wan_networkgroup": "WAN2"},
            ]
        }
        status = WANLoadBalancingStatus(**data)
        assert all(iface.state == "DISCONNECTED" for iface in status.wan_interfaces)

    def test_empty_interfaces(self):
        """Status with no interfaces should be valid."""
        from src.models.wan import WANLoadBalancingStatus

        data = {"wan_interfaces": []}
        status = WANLoadBalancingStatus(**data)
        assert status.wan_interfaces == []


class TestWANProviderCapabilities:
    """Tests for WANProviderCapabilities model."""

    def test_parse_capabilities(self):
        """Parse provider capabilities from enriched config."""
        from src.models.wan import WANProviderCapabilities

        data = {"download_kilobits_per_second": 900000, "upload_kilobits_per_second": 900000}
        caps = WANProviderCapabilities(**data)

        assert caps.download_kilobits_per_second == 900000
        assert caps.upload_kilobits_per_second == 900000

    def test_zero_capabilities(self):
        """Handle zero bandwidth (unconfigured)."""
        from src.models.wan import WANProviderCapabilities

        data = {"download_kilobits_per_second": 0, "upload_kilobits_per_second": 0}
        caps = WANProviderCapabilities(**data)

        assert caps.download_kilobits_per_second == 0
        assert caps.upload_kilobits_per_second == 0

    def test_download_mbps_property(self):
        """Test helper property for Mbps conversion."""
        from src.models.wan import WANProviderCapabilities

        data = {"download_kilobits_per_second": 1000000, "upload_kilobits_per_second": 500000}
        caps = WANProviderCapabilities(**data)

        assert caps.download_mbps == 1000.0
        assert caps.upload_mbps == 500.0


class TestServiceProvider:
    """Tests for ServiceProvider model."""

    def test_parse_provider(self):
        """Parse service provider info from enriched config."""
        from src.models.wan import ServiceProvider

        data = {"city": "Leominster", "name": "Verizon Fios"}
        provider = ServiceProvider(**data)

        assert provider.city == "Leominster"
        assert provider.name == "Verizon Fios"

    def test_empty_provider(self):
        """Parse empty service provider (undetected)."""
        from src.models.wan import ServiceProvider

        data = {}
        provider = ServiceProvider(**data)

        assert provider.city is None
        assert provider.name is None


class TestWANPeakUsage:
    """Tests for WANPeakUsage model."""

    def test_parse_usage(self):
        """Parse peak usage from enriched config."""
        from src.models.wan import WANPeakUsage

        data = {
            "download_percentage": 12.014292005925926,
            "max_rx_bytes-r": 51533988,
            "max_tx_bytes-r": 113635175,
            "upload_percentage": 14.057303268148146,
        }
        usage = WANPeakUsage(**data)

        assert usage.download_percentage == pytest.approx(12.014, rel=0.01)
        assert usage.max_rx_bytes == 51533988
        assert usage.max_tx_bytes == 113635175
        assert usage.upload_percentage == pytest.approx(14.057, rel=0.01)

    def test_negative_values(self):
        """Handle -1 values (no data available)."""
        from src.models.wan import WANPeakUsage

        data = {
            "download_percentage": -1,
            "max_rx_bytes-r": 0,
            "max_tx_bytes-r": 0,
            "upload_percentage": -1,
        }
        usage = WANPeakUsage(**data)

        assert usage.download_percentage == -1
        assert usage.upload_percentage == -1


class TestWANStatistics:
    """Tests for WANStatistics model."""

    def test_parse_statistics(self):
        """Parse WAN statistics from enriched config."""
        from src.models.wan import WANStatistics

        data = {
            "peak_usage": {
                "download_percentage": 12.0,
                "max_rx_bytes-r": 51533988,
                "max_tx_bytes-r": 113635175,
                "upload_percentage": 14.0,
            },
            "uptime_percentage": 100,
        }
        stats = WANStatistics(**data)

        assert stats.uptime_percentage == 100
        assert stats.peak_usage.download_percentage == 12.0

    def test_negative_uptime(self):
        """Handle -1 uptime (no data)."""
        from src.models.wan import WANStatistics

        data = {
            "peak_usage": {
                "download_percentage": -1,
                "max_rx_bytes-r": 0,
                "max_tx_bytes-r": 0,
                "upload_percentage": -1,
            },
            "uptime_percentage": -1,
        }
        stats = WANStatistics(**data)
        assert stats.uptime_percentage == -1


class TestWANDetails:
    """Tests for WANDetails model."""

    def test_parse_details(self):
        """Parse WAN details from enriched config."""
        from src.models.wan import WANDetails

        data = {
            "creation_timestamp": 1695020868,
            "service_provider": {"city": "Leominster", "name": "Verizon Fios"},
        }
        details = WANDetails(**data)

        assert details.creation_timestamp == 1695020868
        assert details.service_provider.name == "Verizon Fios"

    def test_empty_provider(self):
        """Parse details with empty provider."""
        from src.models.wan import WANDetails

        data = {"creation_timestamp": 1695020868, "service_provider": {}}
        details = WANDetails(**data)
        assert details.service_provider.name is None


class TestWANEnrichedConfiguration:
    """Tests for WANEnrichedConfiguration model."""

    def test_parse_enriched_config(self):
        """Parse full enriched WAN configuration."""
        from src.models.wan import WANEnrichedConfiguration

        data = {
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
        }
        config = WANEnrichedConfiguration(**data)

        assert config.configuration.id == "6507f744e35fa70a9663d80c"
        assert config.configuration.name == "Internet 1"
        assert config.details.service_provider.name == "Verizon Fios"
        assert config.statistics.uptime_percentage == 100

    def test_parse_backup_wan(self):
        """Parse backup WAN with minimal data."""
        from src.models.wan import WANEnrichedConfiguration

        data = {
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
        }
        config = WANEnrichedConfiguration(**data)

        assert config.configuration.wan_load_balance_type == "failover-only"
        assert config.statistics.uptime_percentage == -1


class TestWANEnrichedConfig:
    """Tests for WANEnrichedConfig inner model."""

    def test_parse_config(self):
        """Parse WAN configuration from enriched config."""
        from src.models.wan import WANEnrichedConfig

        data = {
            "_id": "6507f744e35fa70a9663d80c",
            "attr_no_delete": True,
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
            "wan_smartq_enabled": False,
            "mac_override_enabled": False,
        }
        config = WANEnrichedConfig(**data)

        assert config.id == "6507f744e35fa70a9663d80c"
        assert config.name == "Internet 1"
        assert config.wan_type == "dhcp"
        assert config.wan_failover_priority == 1
        assert config.wan_load_balance_type == "weighted"
        assert config.wan_load_balance_weight == 50
        assert config.wan_smartq_enabled is False

    def test_optional_fields(self):
        """Optional fields should have defaults."""
        from src.models.wan import WANEnrichedConfig

        data = {
            "_id": "test",
            "name": "Test WAN",
            "purpose": "wan",
            "wan_type": "dhcp",
            "wan_networkgroup": "WAN",
            "wan_failover_priority": 1,
            "wan_provider_capabilities": {
                "download_kilobits_per_second": 0,
                "upload_kilobits_per_second": 0,
            },
        }
        config = WANEnrichedConfig(**data)

        assert config.wan_load_balance_type is None
        assert config.wan_load_balance_weight is None
        assert config.wan_smartq_enabled is None


class TestWANDefaults:
    """Tests for WANDefaults model."""

    def test_parse_defaults(self):
        """Parse WAN defaults from captured schema."""
        from src.models.wan import WANDefaults

        data = {
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
        defaults = WANDefaults(**data)

        assert defaults.purpose == "wan"
        assert defaults.wan_type == "dhcp"
        assert defaults.wan_failover_priority == 0
        assert defaults.wan_dns_preference == "auto"
        assert defaults.wan_smartq_enabled is False

    def test_extra_fields_allowed(self):
        """Extra fields from API should be preserved."""
        from src.models.wan import WANDefaults

        data = {
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
            "some_future_field": "value",  # Should be allowed
        }
        defaults = WANDefaults(**data)
        assert defaults.model_extra.get("some_future_field") == "value"
