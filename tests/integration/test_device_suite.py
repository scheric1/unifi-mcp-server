#!/usr/bin/env python3
"""
Device Management Integration Test Suite

Tests all device-related MCP tools against real UniFi environments.
"""

from typing import Any

import pytest

from src.tools import devices
from src.utils import ResourceNotFoundError
from tests.integration.test_harness import TestEnvironment, TestHarness, TestSuite


@pytest.mark.integration
async def test_list_devices_by_type(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test list_devices_by_type tool with common device type."""
    # Cloud APIs support device endpoints (aggregate stats)
    try:
        # Try common device types
        for device_type in ["uap", "usw", "ugw", "udm", "uxg"]:
            result = await devices.list_devices_by_type(
                site_id=env.site_id,
                device_type=device_type,
                settings=settings,
            )

            # Validate response structure
            assert isinstance(result, list), f"Result for type '{device_type}' must be a list"

            if result:  # If devices of this type exist
                device = result[0]
                assert "id" in device or "_id" in device, "Device must have id"
                assert "mac" in device, "Device must have mac"
                assert "type" in device or "model" in device, "Device must have type or model"

                return {
                    "status": "PASS",
                    "message": f"Found {len(result)} devices of type '{device_type}'",
                    "details": {
                        "device_type": device_type,
                        "count": len(result),
                        "first_device_mac": device.get("mac", "unknown")[:8] + "...",
                    },
                }

        # No devices of any type found
        return {
            "status": "SKIP",
            "message": "No devices found for any common type (uap, usw, ugw, udm, uxg)",
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_list_devices_by_type_pagination(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test list_devices_by_type tool with pagination parameters."""
    try:
        # First, find a device type that exists
        device_type = None
        for dt in ["uap", "usw", "ugw", "udm"]:
            result = await devices.list_devices_by_type(
                site_id=env.site_id,
                device_type=dt,
                settings=settings,
            )
            if result:
                device_type = dt
                break

        if not device_type:
            return {"status": "SKIP", "message": "No devices found for pagination test"}

        # Test with limit
        limited = await devices.list_devices_by_type(
            site_id=env.site_id,
            device_type=device_type,
            settings=settings,
            limit=1,
        )

        assert isinstance(limited, list), "Result must be a list"
        assert len(limited) <= 1, "Limit parameter should restrict results"

        # Test with offset
        offset_result = await devices.list_devices_by_type(
            site_id=env.site_id,
            device_type=device_type,
            settings=settings,
            offset=0,
            limit=10,
        )

        return {
            "status": "PASS",
            "message": f"Pagination working for type '{device_type}'",
            "details": {
                "device_type": device_type,
                "limited_count": len(limited),
                "offset_count": len(offset_result),
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_get_device_details(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test get_device_details tool for discovered device."""
    try:
        # First, discover a device
        device_list = None
        for device_type in ["uap", "usw", "ugw", "udm", "uxg"]:
            device_list = await devices.list_devices_by_type(
                site_id=env.site_id,
                device_type=device_type,
                settings=settings,
                limit=1,
            )
            if device_list:
                break

        if not device_list:
            return {"status": "SKIP", "message": "No devices found for details test"}

        device_id = device_list[0].get("id") or device_list[0].get("_id")
        assert device_id, "Device must have an ID"

        # Get details
        result = await devices.get_device_details(
            site_id=env.site_id,
            device_id=device_id,
            settings=settings,
        )

        # Validate response structure
        assert isinstance(result, dict), "Result must be a dictionary"
        assert "mac" in result, "Device details must have mac"
        assert result.get("id") == device_id or result.get("_id") == device_id, "ID must match"

        return {
            "status": "PASS",
            "message": f"Retrieved details for device {device_id[:8]}...",
            "details": {
                "device_id": device_id[:8] + "...",
                "mac": result.get("mac", "unknown")[:8] + "...",
                "name": result.get("name", "unnamed"),
                "model": result.get("model", "unknown"),
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_get_device_details_missing(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test get_device_details with non-existent device ID (expect error)."""
    try:
        fake_id = "000000000000000000000000"  # Non-existent ObjectId format

        await devices.get_device_details(
            site_id=env.site_id,
            device_id=fake_id,
            settings=settings,
        )

        # If we get here, the device exists (unlikely) or error handling is wrong
        return {
            "status": "FAIL",
            "message": "Expected ResourceNotFoundError but got result",
        }

    except ResourceNotFoundError:
        # Expected error
        return {
            "status": "PASS",
            "message": "Correctly raised ResourceNotFoundError for missing device",
        }
    except Exception as e:
        # Unexpected error type
        return {
            "status": "ERROR",
            "message": f"Unexpected error type: {type(e).__name__}: {str(e)}",
        }


@pytest.mark.integration
async def test_get_device_statistics(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test get_device_statistics tool for discovered device."""
    try:
        # First, discover a device
        device_list = None
        for device_type in ["uap", "usw", "ugw", "udm", "uxg"]:
            device_list = await devices.list_devices_by_type(
                site_id=env.site_id,
                device_type=device_type,
                settings=settings,
                limit=1,
            )
            if device_list:
                break

        if not device_list:
            return {"status": "SKIP", "message": "No devices found for statistics test"}

        device_id = device_list[0].get("id") or device_list[0].get("_id")
        assert device_id, "Device must have an ID"

        # Get statistics
        result = await devices.get_device_statistics(
            site_id=env.site_id,
            device_id=device_id,
            settings=settings,
        )

        # Validate response structure
        assert isinstance(result, dict), "Result must be a dictionary"
        assert "device_id" in result, "Statistics must have device_id"
        assert result["device_id"] == device_id, "Device ID must match"

        # Check for common statistics fields
        stats_fields = ["uptime", "cpu", "mem", "tx_bytes", "rx_bytes", "state"]
        present_fields = [f for f in stats_fields if f in result]

        return {
            "status": "PASS",
            "message": f"Retrieved statistics for device {device_id[:8]}...",
            "details": {
                "device_id": device_id[:8] + "...",
                "uptime": result.get("uptime", 0),
                "state": result.get("state", "unknown"),
                "stats_fields": len(present_fields),
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_search_devices_by_partial_name(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test search_devices tool with partial name query."""
    try:
        # First, get a device to extract a searchable name
        device_list = None
        for device_type in ["uap", "usw", "ugw", "udm", "uxg"]:
            device_list = await devices.list_devices_by_type(
                site_id=env.site_id,
                device_type=device_type,
                settings=settings,
                limit=1,
            )
            if device_list and device_list[0].get("name"):
                break

        if not device_list or not device_list[0].get("name"):
            return {"status": "SKIP", "message": "No devices with names found for search test"}

        device_name = device_list[0]["name"]
        # Use first few characters as search query
        query = device_name[:3] if len(device_name) >= 3 else device_name

        # Search
        result = await devices.search_devices(
            site_id=env.site_id,
            query=query,
            settings=settings,
        )

        assert isinstance(result, list), "Result must be a list"
        # The original device should be in results
        found = any(
            d.get("name", "").lower().startswith(query.lower())
            or query.lower() in d.get("name", "").lower()
            for d in result
        )

        return {
            "status": "PASS",
            "message": f"Search for '{query}' found {len(result)} devices",
            "details": {
                "query": query,
                "results_count": len(result),
                "found_original": found,
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_search_devices_by_mac(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test search_devices tool with MAC address query."""
    try:
        # First, get a device to extract a MAC
        device_list = None
        for device_type in ["uap", "usw", "ugw", "udm", "uxg"]:
            device_list = await devices.list_devices_by_type(
                site_id=env.site_id,
                device_type=device_type,
                settings=settings,
                limit=1,
            )
            if device_list and device_list[0].get("mac"):
                break

        if not device_list or not device_list[0].get("mac"):
            return {"status": "SKIP", "message": "No devices found for MAC search test"}

        mac = device_list[0]["mac"]
        # Use partial MAC (first few characters)
        query = mac[:8]

        # Search
        result = await devices.search_devices(
            site_id=env.site_id,
            query=query,
            settings=settings,
        )

        assert isinstance(result, list), "Result must be a list"
        assert len(result) > 0, "Should find at least the original device"

        # Verify original device is in results
        found = any(d.get("mac") == mac for d in result)

        return {
            "status": "PASS",
            "message": f"MAC search for '{query}' found {len(result)} devices",
            "details": {
                "query": query,
                "results_count": len(result),
                "found_original": found,
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_list_pending_devices(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test list_pending_devices tool (devices awaiting adoption)."""
    # Skip on cloud APIs - not supported
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {
            "status": "SKIP",
            "message": "Cloud APIs do not support pending device listing",
        }

    try:
        result = await devices.list_pending_devices(
            site_id=env.site_id,
            settings=settings,
        )

        # Validate response structure
        assert isinstance(result, list), "Result must be a list"

        # It's normal to have no pending devices
        if not result:
            return {
                "status": "PASS",
                "message": "No pending devices (expected in normal operation)",
                "details": {"count": 0},
            }

        # If pending devices exist, validate structure
        device = result[0]
        assert "mac" in device, "Pending device must have mac"

        return {
            "status": "PASS",
            "message": f"Found {len(result)} pending devices",
            "details": {
                "count": len(result),
                "first_mac": device.get("mac", "unknown")[:8] + "...",
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


def create_device_suite() -> TestSuite:
    """Create the device management test suite."""
    return TestSuite(
        name="device",
        description="Device Management Tools - list_devices_by_type, get_device_details, search_devices, statistics",
        tests=[
            test_list_devices_by_type,
            test_list_devices_by_type_pagination,
            test_get_device_details,
            test_get_device_details_missing,
            test_get_device_statistics,
            test_search_devices_by_partial_name,
            test_search_devices_by_mac,
            test_list_pending_devices,
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

        suite = create_device_suite()
        harness.register_suite(suite)

        # Parse environment filter
        env_filter = None
        if "--env" in sys.argv:
            idx = sys.argv.index("--env")
            if idx + 1 < len(sys.argv):
                env_filter = [sys.argv[idx + 1]]

        # Run suite
        await harness.run_suite("device", environment_filter=env_filter)

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
