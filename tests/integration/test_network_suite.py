#!/usr/bin/env python3
"""
Network Configuration Integration Test Suite

Tests all network-related MCP tools against real UniFi environments.
"""

from typing import Any

import pytest

from src.tools import networks, wifi
from src.utils import ResourceNotFoundError
from tests.integration.test_harness import TestEnvironment, TestHarness, TestSuite


@pytest.mark.integration
async def test_list_vlans(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test list_vlans tool."""
    # Skip on cloud APIs - network configuration not supported
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {
            "status": "SKIP",
            "message": "Cloud APIs do not support network configuration (local only)",
        }

    try:
        result = await networks.list_vlans(
            site_id=env.site_id,
            settings=settings,
        )

        # Validate response structure
        assert isinstance(result, list), "Result must be a list"

        if not result:
            return {
                "status": "SKIP",
                "message": "No VLANs/networks found (site may be unconfigured)",
            }

        # Validate network structure
        network = result[0]
        assert "_id" in network or "id" in network, "Network must have id"
        assert "name" in network, "Network must have name"

        return {
            "status": "PASS",
            "message": f"Listed {len(result)} VLANs/networks",
            "details": {
                "count": len(result),
                "first_network": network.get("name", "unknown"),
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_list_vlans_pagination(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test list_vlans with pagination parameters."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support network configuration"}

    try:
        # Get all networks
        all_networks = await networks.list_vlans(
            site_id=env.site_id,
            settings=settings,
        )

        if not all_networks:
            return {"status": "SKIP", "message": "No networks found for pagination test"}

        # Test with limit
        limited = await networks.list_vlans(
            site_id=env.site_id,
            settings=settings,
            limit=1,
        )

        assert isinstance(limited, list), "Result must be a list"
        assert len(limited) <= 1, "Limit parameter should restrict results"

        return {
            "status": "PASS",
            "message": "Pagination working correctly",
            "details": {
                "total_count": len(all_networks),
                "limited_count": len(limited),
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_get_network_details(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test get_network_details for discovered network."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support network configuration"}

    try:
        # First, discover a network
        network_list = await networks.list_vlans(
            site_id=env.site_id,
            settings=settings,
            limit=1,
        )

        if not network_list:
            return {"status": "SKIP", "message": "No networks found for details test"}

        network_id = network_list[0].get("_id") or network_list[0].get("id")
        assert network_id, "Network must have an ID"

        # Get details
        result = await networks.get_network_details(
            site_id=env.site_id,
            network_id=network_id,
            settings=settings,
        )

        # Validate response structure
        assert isinstance(result, dict), "Result must be a dictionary"
        assert "name" in result, "Network details must have name"
        result_id = result.get("_id") or result.get("id")
        assert result_id == network_id, "ID must match"

        return {
            "status": "PASS",
            "message": f"Retrieved details for network {result.get('name')}",
            "details": {
                "network_id": network_id[:8] + "...",
                "name": result.get("name", "unnamed"),
                "vlan": result.get("vlan"),
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_get_network_details_missing(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test get_network_details with non-existent network ID (expect error)."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support network configuration"}

    try:
        fake_id = "000000000000000000000000"  # Non-existent ObjectId format

        await networks.get_network_details(
            site_id=env.site_id,
            network_id=fake_id,
            settings=settings,
        )

        # If we get here, error handling is wrong
        return {
            "status": "FAIL",
            "message": "Expected ResourceNotFoundError but got result",
        }

    except ResourceNotFoundError:
        # Expected error
        return {
            "status": "PASS",
            "message": "Correctly raised ResourceNotFoundError for missing network",
        }
    except Exception as e:
        # Unexpected error type
        return {
            "status": "ERROR",
            "message": f"Unexpected error type: {type(e).__name__}: {str(e)}",
        }


@pytest.mark.integration
async def test_list_wlans(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test list_wlans tool (wireless networks/SSIDs)."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support WLAN configuration"}

    try:
        result = await wifi.list_wlans(
            site_id=env.site_id,
            settings=settings,
        )

        # Validate response structure
        assert isinstance(result, list), "Result must be a list"

        if not result:
            return {
                "status": "SKIP",
                "message": "No WLANs/SSIDs found (site may have no wireless networks)",
            }

        # Validate WLAN structure
        wlan = result[0]
        assert "_id" in wlan or "id" in wlan, "WLAN must have id"
        assert "name" in wlan, "WLAN must have name"

        return {
            "status": "PASS",
            "message": f"Listed {len(result)} wireless networks",
            "details": {
                "count": len(result),
                "first_ssid": wlan.get("name", "unknown"),
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_get_subnet_info(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test get_subnet_info for discovered network."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support network configuration"}

    try:
        # First, discover a network
        network_list = await networks.list_vlans(
            site_id=env.site_id,
            settings=settings,
        )

        if not network_list:
            return {"status": "SKIP", "message": "No networks found for subnet info test"}

        network_id = network_list[0].get("_id") or network_list[0].get("id")
        assert network_id, "Network must have an ID"

        # Get subnet info
        result = await networks.get_subnet_info(
            site_id=env.site_id,
            network_id=network_id,
            settings=settings,
        )

        # Validate response structure
        assert isinstance(result, dict), "Result must be a dictionary"
        assert "network_id" in result, "Subnet info must have network_id"

        # Check for common subnet fields
        subnet_fields = ["subnet", "gateway", "netmask", "dhcp_enabled"]
        present_fields = [f for f in subnet_fields if f in result]

        return {
            "status": "PASS",
            "message": f"Retrieved subnet info for network {network_id[:8]}...",
            "details": {
                "network_id": network_id[:8] + "...",
                "subnet": result.get("subnet", "unknown"),
                "gateway": result.get("gateway", "unknown"),
                "fields_present": len(present_fields),
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_get_network_statistics(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test get_network_statistics for site."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support network statistics"}

    try:
        result = await networks.get_network_statistics(
            site_id=env.site_id,
            settings=settings,
        )

        # Validate response structure
        assert isinstance(result, dict), "Result must be a dictionary"

        # Check for common statistics fields
        stats_fields = [
            "total_networks",
            "total_vlans",
            "total_bytes",
            "total_packets",
        ]
        present_fields = [f for f in stats_fields if f in result]

        return {
            "status": "PASS",
            "message": "Retrieved network statistics",
            "details": {
                "total_networks": result.get("total_networks", 0),
                "stats_fields": len(present_fields),
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


def create_network_suite() -> TestSuite:
    """Create the network configuration test suite."""
    return TestSuite(
        name="network",
        description="Network Configuration Tools - list_vlans, get_network_details, list_wlans, subnet_info, statistics",
        tests=[
            test_list_vlans,
            test_list_vlans_pagination,
            test_get_network_details,
            test_get_network_details_missing,
            test_list_wlans,
            test_get_subnet_info,
            test_get_network_statistics,
        ],
    )


# CLI entry point
if __name__ == "__main__":
    import asyncio
    import sys
    from pathlib import Path

    async def main():
        harness = TestHarness()
        harness.verbose = "--verbose" in sys.argv or "-v" in sys.argv

        suite = create_network_suite()
        harness.register_suite(suite)

        # Parse environment filter
        env_filter = None
        if "--env" in sys.argv:
            idx = sys.argv.index("--env")
            if idx + 1 < len(sys.argv):
                env_filter = [sys.argv[idx + 1]]

        # Run suite
        await harness.run_suite("network", environment_filter=env_filter)

        # Print summary
        harness.print_summary()

        # Export results if requested
        if "--export" in sys.argv:
            idx = sys.argv.index("--export")
            output_file = (
                Path(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) else Path("test_results.json")
            )
            harness.export_results(output_file)

        # Exit with error code if any tests failed
        failed_count = sum(1 for r in harness.results if r.status.value in ["FAIL", "ERROR"])
        sys.exit(1 if failed_count > 0 else 0)

    asyncio.run(main())
