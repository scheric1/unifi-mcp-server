#!/usr/bin/env python3
"""
Client Operations Integration Test Suite

Tests all client operation MCP tools against real UniFi environments.
DRY-RUN ONLY for safety - these operations affect user connectivity.
"""

from typing import Any

import pytest

from src.tools import client_management
from src.utils import ValidationError
from tests.integration.test_harness import TestEnvironment, TestSuite


@pytest.mark.integration
async def test_block_client_without_confirmation(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test block_client without confirmation flag (should fail)."""
    # Skip on cloud APIs - client management is local only
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {
            "status": "SKIP",
            "message": "Cloud APIs do not support client management operations (local only)",
        }

    try:
        # Attempt to block without confirm=True (using fake MAC)
        await client_management.block_client(
            site_id=env.site_id,
            client_mac="00:00:00:00:00:01",  # Fake MAC for validation test
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
        if "confirmation" in str(e).lower() or "confirm" in str(e).lower():
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


@pytest.mark.integration
async def test_block_client_dry_run(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test block_client in dry-run mode (safe validation)."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support client management"}

    try:
        # Use fake MAC address for dry-run test (doesn't need to exist)
        result = await client_management.block_client(
            site_id=env.site_id,
            client_mac="00:11:22:33:44:55",  # Test MAC
            settings=settings,
            confirm=True,
            dry_run=True,  # DRY-RUN ONLY - never actually block
        )

        assert result.get("dry_run") is True, "Must be dry-run mode"
        assert "would_block" in result, "Should indicate planned action"

        return {
            "status": "PASS",
            "message": "Dry-run validation successful (client not blocked)",
            "details": {"dry_run": True, "operation": "block"},
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_unblock_client_dry_run(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test unblock_client in dry-run mode (safe validation)."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support client management"}

    try:
        # Use fake MAC address for dry-run test
        result = await client_management.unblock_client(
            site_id=env.site_id,
            client_mac="00:11:22:33:44:55",  # Test MAC
            settings=settings,
            confirm=True,
            dry_run=True,  # DRY-RUN ONLY - never actually unblock
        )

        assert result.get("dry_run") is True, "Must be dry-run mode"
        assert "would_unblock" in result, "Should indicate planned action"

        return {
            "status": "PASS",
            "message": "Dry-run validation successful (client not unblocked)",
            "details": {"dry_run": True, "operation": "unblock"},
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_reconnect_client_dry_run(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test reconnect_client in dry-run mode (safe validation)."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support client management"}

    try:
        # Use fake MAC address for dry-run test
        result = await client_management.reconnect_client(
            site_id=env.site_id,
            client_mac="00:11:22:33:44:55",  # Test MAC
            settings=settings,
            confirm=True,
            dry_run=True,  # DRY-RUN ONLY - never actually reconnect
        )

        assert result.get("dry_run") is True, "Must be dry-run mode"
        assert "would_reconnect" in result, "Should indicate planned action"

        return {
            "status": "PASS",
            "message": "Dry-run validation successful (client not disconnected)",
            "details": {"dry_run": True, "operation": "reconnect"},
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


def create_client_ops_suite() -> TestSuite:
    """Create the client operations test suite."""
    return TestSuite(
        name="client-ops",
        description="Client Operations Tools - block, unblock, reconnect (DRY-RUN ONLY for safety)",
        tests=[
            test_block_client_without_confirmation,
            test_block_client_dry_run,
            test_unblock_client_dry_run,
            test_reconnect_client_dry_run,
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

        suite = create_client_ops_suite()
        harness.register_suite(suite)

        # Parse environment filter
        env_filter = None
        if "--env" in sys.argv:
            idx = sys.argv.index("--env")
            if idx + 1 < len(sys.argv):
                env_filter = [sys.argv[idx + 1]]

        # Run suite
        await harness.run_suite("client-ops", environment_filter=env_filter)

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
