#!/usr/bin/env python3
"""
Device Operations Integration Test Suite

Tests all device operation MCP tools against real UniFi environments.
DRY-RUN ONLY for safety - these operations cause service disruption.
"""

from typing import Any

import pytest

from src.tools import device_control, devices
from src.utils import ValidationError
from tests.integration.test_harness import TestEnvironment, TestSuite


@pytest.mark.integration
async def test_restart_device_without_confirmation(
    settings, env: TestEnvironment
) -> dict[str, Any]:
    """Test restart_device without confirmation flag (should fail)."""
    # Skip on cloud APIs - device management is local only
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {
            "status": "SKIP",
            "message": "Cloud APIs do not support device operations (local only)",
        }

    try:
        # Attempt to restart without confirm=True (using fake MAC)
        await device_control.restart_device(
            site_id=env.site_id,
            device_mac="00:00:00:00:00:01",  # Fake MAC for validation test
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
async def test_restart_device_dry_run(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test restart_device in dry-run mode (safe validation)."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support device operations"}

    try:
        # Use fake MAC address for dry-run test (doesn't need to exist)
        result = await device_control.restart_device(
            site_id=env.site_id,
            device_mac="00:11:22:33:44:55",  # Test MAC
            settings=settings,
            confirm=True,
            dry_run=True,  # DRY-RUN ONLY - NEVER actually restart
        )

        assert result.get("dry_run") is True, "Must be dry-run mode"
        assert "would_restart" in result, "Should indicate planned action"

        return {
            "status": "PASS",
            "message": "Dry-run validation successful (device not restarted)",
            "details": {"dry_run": True, "operation": "restart"},
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_locate_device_dry_run(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test locate_device in dry-run mode (safe validation)."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support device operations"}

    try:
        # Use fake MAC address for dry-run test
        result = await device_control.locate_device(
            site_id=env.site_id,
            device_mac="00:11:22:33:44:55",  # Test MAC
            settings=settings,
            enabled=True,
            confirm=True,
            dry_run=True,  # DRY-RUN ONLY - never actually enable locate
        )

        assert result.get("dry_run") is True, "Must be dry-run mode"
        assert (
            "would_enable" in result or "would_disable" in result
        ), "Should indicate planned action"

        return {
            "status": "PASS",
            "message": "Dry-run validation successful (locate mode not changed)",
            "details": {"dry_run": True, "operation": "locate"},
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_upgrade_device_dry_run(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test upgrade_device in dry-run mode (safe validation)."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support device operations"}

    try:
        # Use fake MAC address for dry-run test
        result = await device_control.upgrade_device(
            site_id=env.site_id,
            device_mac="00:11:22:33:44:55",  # Test MAC
            settings=settings,
            confirm=True,
            dry_run=True,  # DRY-RUN ONLY - NEVER actually upgrade
        )

        assert result.get("dry_run") is True, "Must be dry-run mode"
        assert "would_upgrade" in result, "Should indicate planned action"

        return {
            "status": "PASS",
            "message": "Dry-run validation successful (device not upgraded)",
            "details": {"dry_run": True, "operation": "upgrade"},
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_adopt_device_dry_run(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test adopt_device in dry-run mode (safe validation)."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support device operations"}

    try:
        # Use fake device ID for dry-run test (doesn't need to exist)
        # Device ID must be 24-char hex string (MongoDB ObjectId format)
        result = await devices.adopt_device(
            site_id=env.site_id,
            device_id="000000000000000000000001",  # Valid format fake ID
            settings=settings,
            confirm=True,
            dry_run=True,  # DRY-RUN ONLY - never actually adopt
        )

        assert result.get("dry_run") is True, "Must be dry-run mode"
        assert "would_adopt" in result or "device_id" in result, "Should indicate planned action"

        return {
            "status": "PASS",
            "message": "Dry-run validation successful (device not adopted)",
            "details": {"dry_run": True, "operation": "adopt"},
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


def create_device_ops_suite() -> TestSuite:
    """Create the device operations test suite."""
    return TestSuite(
        name="device-ops",
        description="Device Operations Tools - restart, locate, upgrade, adopt (DRY-RUN ONLY for safety)",
        tests=[
            test_restart_device_without_confirmation,
            test_restart_device_dry_run,
            test_locate_device_dry_run,
            test_upgrade_device_dry_run,
            test_adopt_device_dry_run,
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

        suite = create_device_ops_suite()
        harness.register_suite(suite)

        # Parse environment filter
        env_filter = None
        if "--env" in sys.argv:
            idx = sys.argv.index("--env")
            if idx + 1 < len(sys.argv):
                env_filter = [sys.argv[idx + 1]]

        # Run suite
        await harness.run_suite("device-ops", environment_filter=env_filter)

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
