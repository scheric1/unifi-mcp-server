#!/usr/bin/env python3
"""
Traffic Flow Monitoring Integration Test Suite

Tests all traffic flow monitoring MCP tools against real UniFi environments.
All operations are read-only except blocking operations (dry-run only).
"""

from typing import Any

import pytest

from src.tools import traffic_flows
from src.utils import ValidationError
from tests.integration.test_harness import TestEnvironment, TestSuite


@pytest.mark.integration
async def test_get_traffic_flows(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test get_traffic_flows tool."""
    # Skip on cloud APIs - traffic flows are local only
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {
            "status": "SKIP",
            "message": "Cloud APIs do not support traffic flows (local only)",
        }

    try:
        result = await traffic_flows.get_traffic_flows(
            site_id=env.site_id,
            settings=settings,
            time_range="24h",
        )

        # Validate response structure
        assert isinstance(result, list), "Result must be a list"

        # May be empty if no traffic
        if not result:
            return {
                "status": "SKIP",
                "message": "No traffic flows found (network may be idle)",
            }

        # Validate flow structure
        flow = result[0]
        assert "flow_id" in flow, "Flow must have flow_id"
        assert "source_ip" in flow, "Flow must have source_ip"
        assert "destination_ip" in flow, "Flow must have destination_ip"

        return {
            "status": "PASS",
            "message": f"Retrieved {len(result)} traffic flows",
            "details": {
                "count": len(result),
                "has_protocol": "protocol" in flow,
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        # Traffic flows endpoint may not be available
        error_msg = str(e).lower()
        if "not available" in error_msg or "404" in error_msg:
            return {
                "status": "SKIP",
                "message": "Traffic flows endpoint not available on this API version",
            }
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_get_flow_statistics(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test get_flow_statistics tool."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support traffic flows"}

    try:
        result = await traffic_flows.get_flow_statistics(
            site_id=env.site_id,
            settings=settings,
            time_range="24h",
        )

        # Validate response structure
        assert isinstance(result, dict), "Result must be a dictionary"
        assert "site_id" in result, "Must have site_id"
        assert "total_flows" in result, "Must have total_flows"
        assert "total_bytes" in result, "Must have total_bytes"

        return {
            "status": "PASS",
            "message": "Retrieved flow statistics",
            "details": {
                "total_flows": result.get("total_flows", 0),
                "total_bytes": result.get("total_bytes", 0),
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        error_msg = str(e).lower()
        if "not available" in error_msg or "404" in error_msg:
            return {
                "status": "SKIP",
                "message": "Flow statistics endpoint not available",
            }
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_get_top_flows(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test get_top_flows tool."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support traffic flows"}

    try:
        result = await traffic_flows.get_top_flows(
            site_id=env.site_id,
            settings=settings,
            limit=5,
            time_range="24h",
        )

        # Validate response structure
        assert isinstance(result, list), "Result must be a list"

        if not result:
            return {
                "status": "SKIP",
                "message": "No top flows found (network may be idle)",
            }

        # Verify limit is respected
        assert len(result) <= 5, "Result should respect limit parameter"

        flow = result[0]
        assert "flow_id" in flow, "Flow must have flow_id"

        return {
            "status": "PASS",
            "message": f"Retrieved top {len(result)} flows",
            "details": {"count": len(result)},
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        error_msg = str(e).lower()
        if "not available" in error_msg or "404" in error_msg:
            return {
                "status": "SKIP",
                "message": "Top flows endpoint not available",
            }
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_get_traffic_flows_with_filters(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test get_traffic_flows with protocol filter."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support traffic flows"}

    try:
        # Test with TCP protocol filter
        result = await traffic_flows.get_traffic_flows(
            site_id=env.site_id,
            settings=settings,
            protocol="tcp",
            time_range="24h",
        )

        assert isinstance(result, list), "Result must be a list"

        # If results exist, verify they match filter
        if result:
            for flow in result:
                if "protocol" in flow:
                    assert flow["protocol"].lower() == "tcp", "All flows should be TCP"

        return {
            "status": "PASS",
            "message": f"Protocol filter working: found {len(result)} TCP flows",
            "details": {"protocol": "tcp", "count": len(result)},
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        error_msg = str(e).lower()
        if "not available" in error_msg or "404" in error_msg:
            return {
                "status": "SKIP",
                "message": "Traffic flows endpoint not available",
            }
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_get_flow_risks(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test get_flow_risks tool."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support traffic flows"}

    try:
        result = await traffic_flows.get_flow_risks(
            site_id=env.site_id,
            settings=settings,
            time_range="24h",
        )

        # Validate response structure
        assert isinstance(result, list), "Result must be a list"

        # May be empty if no risky flows
        if not result:
            return {
                "status": "SKIP",
                "message": "No flow risks found (all traffic appears safe)",
            }

        risk = result[0]
        assert "flow_id" in risk, "Risk must have flow_id"
        assert "risk_level" in risk, "Risk must have risk_level"

        return {
            "status": "PASS",
            "message": f"Retrieved {len(result)} flow risks",
            "details": {"count": len(result)},
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        error_msg = str(e).lower()
        if "not available" in error_msg or "404" in error_msg:
            return {
                "status": "SKIP",
                "message": "Flow risks endpoint not available",
            }
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_get_flow_trends(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test get_flow_trends tool."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support traffic flows"}

    try:
        result = await traffic_flows.get_flow_trends(
            site_id=env.site_id,
            settings=settings,
            time_range="7d",
            interval="1h",
        )

        # Validate response structure
        assert isinstance(result, list), "Result must be a list"

        # May be empty if endpoint not supported
        if not result:
            return {
                "status": "SKIP",
                "message": "No flow trends data available",
            }

        return {
            "status": "PASS",
            "message": f"Retrieved {len(result)} trend data points",
            "details": {"data_points": len(result)},
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        error_msg = str(e).lower()
        if "not available" in error_msg or "404" in error_msg:
            return {
                "status": "SKIP",
                "message": "Flow trends endpoint not available",
            }
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_get_connection_states(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test get_connection_states tool."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support traffic flows"}

    try:
        result = await traffic_flows.get_connection_states(
            site_id=env.site_id,
            settings=settings,
            time_range="1h",
        )

        # Validate response structure
        assert isinstance(result, list), "Result must be a list"

        if not result:
            return {
                "status": "SKIP",
                "message": "No connection states found (network may be idle)",
            }

        state = result[0]
        assert "flow_id" in state, "State must have flow_id"
        assert "state" in state, "State must have state field"

        # Count active vs closed connections
        active = sum(1 for s in result if s.get("state") == "active")
        closed = sum(1 for s in result if s.get("state") == "closed")

        return {
            "status": "PASS",
            "message": f"Retrieved {len(result)} connection states",
            "details": {
                "total": len(result),
                "active": active,
                "closed": closed,
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        error_msg = str(e).lower()
        if "not available" in error_msg or "404" in error_msg:
            return {
                "status": "SKIP",
                "message": "Connection states endpoint not available",
            }
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_get_client_flow_aggregation(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test get_client_flow_aggregation for discovered client."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support traffic flows"}

    try:
        # First, discover a client
        from src.tools import clients

        client_list = await clients.list_active_clients(
            site_id=env.site_id,
            settings=settings,
            limit=1,
        )

        if not client_list:
            return {"status": "SKIP", "message": "No clients found for aggregation test"}

        client_mac = client_list[0].get("mac")
        assert client_mac, "Client must have a MAC address"

        # Get client flow aggregation
        result = await traffic_flows.get_client_flow_aggregation(
            site_id=env.site_id,
            client_mac=client_mac,
            settings=settings,
            time_range="24h",
        )

        # Validate response structure
        assert isinstance(result, dict), "Result must be a dictionary"
        assert "client_mac" in result, "Must have client_mac"
        assert result.get("client_mac") == client_mac, "MAC must match"
        assert "total_flows" in result, "Must have total_flows"

        return {
            "status": "PASS",
            "message": f"Retrieved aggregation for client {client_mac[:8]}...",
            "details": {
                "client_mac": client_mac[:8] + "...",
                "total_flows": result.get("total_flows", 0),
                "total_bytes": result.get("total_bytes", 0),
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        error_msg = str(e).lower()
        if "not available" in error_msg or "404" in error_msg:
            return {
                "status": "SKIP",
                "message": "Client flow aggregation endpoint not available",
            }
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_get_flow_analytics(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test get_flow_analytics tool."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support traffic flows"}

    try:
        result = await traffic_flows.get_flow_analytics(
            site_id=env.site_id,
            settings=settings,
            time_range="24h",
        )

        # Validate response structure
        assert isinstance(result, dict), "Result must be a dictionary"
        assert "site_id" in result, "Must have site_id"
        assert "statistics" in result, "Must have statistics"
        assert "protocol_distribution" in result, "Must have protocol_distribution"
        assert "total_flows" in result, "Must have total_flows"

        return {
            "status": "PASS",
            "message": "Retrieved comprehensive flow analytics",
            "details": {
                "total_flows": result.get("total_flows", 0),
                "protocol_count": len(result.get("protocol_distribution", {})),
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        error_msg = str(e).lower()
        if "not available" in error_msg or "404" in error_msg:
            return {
                "status": "SKIP",
                "message": "Flow analytics endpoint not available",
            }
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_export_traffic_flows_json(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test export_traffic_flows in JSON format."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support traffic flows"}

    try:
        result = await traffic_flows.export_traffic_flows(
            site_id=env.site_id,
            settings=settings,
            export_format="json",
            time_range="1h",
            max_records=10,
        )

        # Validate response
        assert isinstance(result, str), "Result must be a string"
        assert len(result) > 0, "Export should not be empty"

        # Verify it's valid JSON
        import json

        parsed = json.loads(result)
        assert isinstance(parsed, list), "Parsed JSON must be a list"

        return {
            "status": "PASS",
            "message": f"Exported {len(parsed)} flows to JSON",
            "details": {"format": "json", "records": len(parsed)},
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        error_msg = str(e).lower()
        if "not available" in error_msg or "404" in error_msg:
            return {
                "status": "SKIP",
                "message": "Traffic flows export not available",
            }
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_block_flow_source_ip_without_confirmation(
    settings, env: TestEnvironment
) -> dict[str, Any]:
    """Test block_flow_source_ip without confirmation flag (should fail)."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support traffic flows"}

    try:
        # Attempt to block without confirm=True
        await traffic_flows.block_flow_source_ip(
            site_id=env.site_id,
            flow_id="test_flow_id",
            settings=settings,
            confirm=False,  # Should raise error
        )

        # If we get here, confirmation check failed
        return {
            "status": "FAIL",
            "message": "Expected ValidationError but got result",
        }

    except ValidationError as e:
        # Expected error
        if "requires confirmation" in str(e):
            return {
                "status": "PASS",
                "message": "Correctly raised ValidationError without confirmation",
            }
        return {"status": "FAIL", "message": f"Unexpected ValidationError: {str(e)}"}
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Unexpected error type: {type(e).__name__}: {str(e)}",
        }


def create_traffic_flows_suite() -> TestSuite:
    """Create the traffic flows monitoring test suite."""
    return TestSuite(
        name="traffic-flows",
        description="Traffic Flow Monitoring Tools - flows, statistics, analytics, risks, aggregation",
        tests=[
            test_get_traffic_flows,
            test_get_flow_statistics,
            test_get_top_flows,
            test_get_traffic_flows_with_filters,
            test_get_flow_risks,
            test_get_flow_trends,
            test_get_connection_states,
            test_get_client_flow_aggregation,
            test_get_flow_analytics,
            test_export_traffic_flows_json,
            test_block_flow_source_ip_without_confirmation,
        ],
    )


# CLI entry point
if __name__ == "__main__":
    import asyncio
    import sys
    from pathlib import Path

    async def main():
        from tests.integration.test_harness import TestHarness

        harness = TestHarness()
        harness.verbose = "--verbose" in sys.argv or "-v" in sys.argv

        suite = create_traffic_flows_suite()
        harness.register_suite(suite)

        # Parse environment filter
        env_filter = None
        if "--env" in sys.argv:
            idx = sys.argv.index("--env")
            if idx + 1 < len(sys.argv):
                env_filter = [sys.argv[idx + 1]]

        # Run suite
        await harness.run_suite("traffic-flows", environment_filter=env_filter)

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
