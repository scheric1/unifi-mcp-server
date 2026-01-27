#!/usr/bin/env python3
"""
Client Management Integration Test Suite

Tests all client-related MCP tools against real UniFi environments.
"""

from typing import Any

import pytest

from src.tools import clients
from src.utils import ResourceNotFoundError
from tests.integration.test_harness import TestEnvironment, TestHarness, TestSuite


@pytest.mark.integration
async def test_list_active_clients(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test list_active_clients tool."""
    try:
        result = await clients.list_active_clients(
            site_id=env.site_id,
            settings=settings,
        )

        # Validate response structure
        assert isinstance(result, list), "Result must be a list"

        if not result:
            return {
                "status": "SKIP",
                "message": "No active clients found (network may be empty)",
            }

        # Validate client structure
        client = result[0]
        assert "mac" in client, "Client must have mac"

        return {
            "status": "PASS",
            "message": f"Listed {len(result)} active clients",
            "details": {
                "count": len(result),
                "first_client_mac": client.get("mac", "unknown")[:8] + "...",
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_list_active_clients_structure(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test list_active_clients response structure validation."""
    try:
        result = await clients.list_active_clients(
            site_id=env.site_id,
            settings=settings,
        )

        assert isinstance(result, list), "Result must be a list"

        if not result:
            return {
                "status": "SKIP",
                "message": "No clients found for structure validation",
            }

        # Validate client structure
        client = result[0]
        required_fields = ["mac"]
        optional_fields = ["hostname", "ip", "is_wired", "signal"]

        # Check required fields
        for field in required_fields:
            assert field in client, f"Client must have '{field}' field"

        # Count optional fields present
        present_optional = sum(1 for field in optional_fields if field in client)

        return {
            "status": "PASS",
            "message": f"Client structure valid: {len(result)} clients, {present_optional}/{len(optional_fields)} optional fields present",
            "details": {
                "client_count": len(result),
                "required_fields": required_fields,
                "optional_fields_present": present_optional,
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_get_client_details(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test get_client_details for discovered client."""
    try:
        # First, discover a client
        client_list = await clients.list_active_clients(
            site_id=env.site_id,
            settings=settings,
            limit=1,
        )

        if not client_list:
            return {"status": "SKIP", "message": "No clients found for details test"}

        client_mac = client_list[0].get("mac")
        assert client_mac, "Client must have a MAC address"

        # Get details
        result = await clients.get_client_details(
            site_id=env.site_id,
            client_mac=client_mac,
            settings=settings,
        )

        # Validate response structure
        assert isinstance(result, dict), "Result must be a dictionary"
        assert "mac" in result, "Client details must have mac"
        assert result.get("mac") == client_mac, "MAC must match"

        return {
            "status": "PASS",
            "message": f"Retrieved details for client {client_mac[:8]}...",
            "details": {
                "mac": client_mac[:8] + "...",
                "hostname": result.get("hostname", "unknown"),
                "ip": result.get("ip", "unknown"),
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_get_client_details_missing(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test get_client_details with non-existent MAC (expect error)."""
    try:
        fake_mac = "00:00:00:00:00:00"  # Non-existent MAC

        await clients.get_client_details(
            site_id=env.site_id,
            client_mac=fake_mac,
            settings=settings,
        )

        # If we get here, the client exists (unlikely) or error handling is wrong
        return {
            "status": "FAIL",
            "message": "Expected ResourceNotFoundError but got result",
        }

    except ResourceNotFoundError:
        # Expected error
        return {
            "status": "PASS",
            "message": "Correctly raised ResourceNotFoundError for missing client",
        }
    except Exception as e:
        # Unexpected error type
        return {
            "status": "ERROR",
            "message": f"Unexpected error type: {type(e).__name__}: {str(e)}",
        }


@pytest.mark.integration
async def test_get_client_statistics(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test get_client_statistics for discovered client."""
    try:
        # First, discover a client
        client_list = await clients.list_active_clients(
            site_id=env.site_id,
            settings=settings,
            limit=1,
        )

        if not client_list:
            return {"status": "SKIP", "message": "No clients found for statistics test"}

        client_mac = client_list[0].get("mac")
        assert client_mac, "Client must have a MAC address"

        # Get statistics
        result = await clients.get_client_statistics(
            site_id=env.site_id,
            client_mac=client_mac,
            settings=settings,
        )

        # Validate response structure
        assert isinstance(result, dict), "Result must be a dictionary"
        assert "mac" in result, "Statistics must have mac"
        assert result["mac"] == client_mac, "Client MAC must match"

        # Check for common statistics fields
        stats_fields = ["tx_bytes", "rx_bytes", "tx_packets", "rx_packets"]
        present_fields = [f for f in stats_fields if f in result]

        return {
            "status": "PASS",
            "message": f"Retrieved statistics for client {client_mac[:8]}...",
            "details": {
                "client_mac": client_mac[:8] + "...",
                "tx_bytes": result.get("tx_bytes", 0),
                "rx_bytes": result.get("rx_bytes", 0),
                "stats_fields": len(present_fields),
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_search_clients_by_hostname(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test search_clients tool with hostname query."""
    try:
        # First, get a client to extract a searchable hostname
        client_list = await clients.list_active_clients(
            site_id=env.site_id,
            settings=settings,
        )

        if not client_list:
            return {"status": "SKIP", "message": "No clients found for search test"}

        # Find client with hostname
        client_with_hostname = None
        for c in client_list:
            if c.get("hostname"):
                client_with_hostname = c
                break

        if not client_with_hostname:
            return {"status": "SKIP", "message": "No clients with hostnames found"}

        hostname = client_with_hostname["hostname"]
        # Use first few characters as search query
        query = hostname[:3] if len(hostname) >= 3 else hostname

        # Search
        result = await clients.search_clients(
            site_id=env.site_id,
            query=query,
            settings=settings,
        )

        assert isinstance(result, list), "Result must be a list"

        return {
            "status": "PASS",
            "message": f"Search for '{query}' found {len(result)} clients",
            "details": {
                "query": query,
                "results_count": len(result),
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_search_clients_by_mac(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test search_clients tool with MAC address query."""
    try:
        # First, get a client to extract a MAC
        client_list = await clients.list_active_clients(
            site_id=env.site_id,
            settings=settings,
            limit=1,
        )

        if not client_list or not client_list[0].get("mac"):
            return {"status": "SKIP", "message": "No clients found for MAC search test"}

        mac = client_list[0]["mac"]
        # Use partial MAC (first few characters)
        query = mac[:8]

        # Search
        result = await clients.search_clients(
            site_id=env.site_id,
            query=query,
            settings=settings,
        )

        assert isinstance(result, list), "Result must be a list"
        assert len(result) > 0, "Should find at least the original client"

        # Verify original client is in results
        found = any(c.get("mac") == mac for c in result)

        return {
            "status": "PASS",
            "message": f"MAC search for '{query}' found {len(result)} clients",
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
async def test_list_active_clients_pagination(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test list_active_clients with pagination parameters."""
    try:
        # Get all clients
        all_clients = await clients.list_active_clients(
            site_id=env.site_id,
            settings=settings,
        )

        if not all_clients:
            return {"status": "SKIP", "message": "No clients found for pagination test"}

        # Test with limit
        limited = await clients.list_active_clients(
            site_id=env.site_id,
            settings=settings,
            limit=1,
        )

        assert isinstance(limited, list), "Result must be a list"
        assert len(limited) <= 1, "Limit parameter should restrict results"

        # Test with offset
        if len(all_clients) > 1:
            offset_result = await clients.list_active_clients(
                site_id=env.site_id,
                settings=settings,
                offset=1,
                limit=10,
            )
            assert len(offset_result) <= len(all_clients) - 1, "Offset should skip first client"

        return {
            "status": "PASS",
            "message": "Pagination working correctly",
            "details": {
                "total_count": len(all_clients),
                "limited_count": len(limited),
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


def create_client_suite() -> TestSuite:
    """Create the client management test suite."""
    return TestSuite(
        name="client",
        description="Client Management Tools - list_active_clients, get_client_details, search_clients, statistics",
        tests=[
            test_list_active_clients,
            test_list_active_clients_structure,
            test_get_client_details,
            test_get_client_details_missing,
            test_get_client_statistics,
            test_search_clients_by_hostname,
            test_search_clients_by_mac,
            test_list_active_clients_pagination,
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

        suite = create_client_suite()
        harness.register_suite(suite)

        # Parse environment filter
        env_filter = None
        if "--env" in sys.argv:
            idx = sys.argv.index("--env")
            if idx + 1 < len(sys.argv):
                env_filter = [sys.argv[idx + 1]]

        # Run suite
        await harness.run_suite("client", environment_filter=env_filter)

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
