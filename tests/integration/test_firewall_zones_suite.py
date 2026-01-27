#!/usr/bin/env python3
"""
Firewall Zones Integration Test Suite

Tests all firewall zone-related MCP tools against real UniFi environments.
Implements create-test-delete pattern with automatic cleanup.
"""

from typing import Any

import pytest

from src.tools import firewall_zones
from src.utils import ValidationError
from tests.integration.test_harness import TestEnvironment, TestSuite

# Test resource prefix
TEST_PREFIX = "TEST_INTEGRATION_"


@pytest.mark.integration
async def test_local_api_requirement(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test that firewall zones require local API (should fail on cloud APIs)."""
    # This test verifies the API type check works correctly
    if env.api_type == "local":
        return {
            "status": "SKIP",
            "message": "Test only validates cloud API rejection (running on local API)",
        }

    try:
        # Attempt to list zones on cloud API (should raise ValidationError)
        await firewall_zones.list_firewall_zones(
            site_id=env.site_id,
            settings=settings,
        )

        # If we get here, the local API check failed
        return {
            "status": "FAIL",
            "message": "Expected ValidationError for cloud API but got result",
        }

    except ValidationError as e:
        # Expected error
        if "local" in str(e).lower() or "zone-based firewall" in str(e).lower():
            return {
                "status": "PASS",
                "message": "Correctly raised ValidationError for cloud API access",
            }
        return {"status": "FAIL", "message": f"Unexpected ValidationError: {str(e)}"}
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Unexpected error type: {type(e).__name__}: {str(e)}",
        }


@pytest.mark.integration
async def test_list_firewall_zones(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test list_firewall_zones tool."""
    # Skip on cloud APIs - zones are local only
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {
            "status": "SKIP",
            "message": "Cloud APIs do not support firewall zones (local only)",
        }

    try:
        result = await firewall_zones.list_firewall_zones(
            site_id=env.site_id,
            settings=settings,
        )

        # Validate response structure
        assert isinstance(result, list), "Result must be a list"

        if not result:
            return {
                "status": "SKIP",
                "message": "No firewall zones found (site may be unconfigured)",
            }

        # Validate zone structure
        zone = result[0]
        assert "id" in zone or "_id" in zone, "Zone must have id or _id"
        assert "name" in zone, "Zone must have name"

        return {
            "status": "PASS",
            "message": f"Listed {len(result)} firewall zones",
            "details": {
                "count": len(result),
                "first_zone": zone.get("name", "unnamed"),
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_create_firewall_zone_without_confirmation(
    settings, env: TestEnvironment
) -> dict[str, Any]:
    """Test create_firewall_zone without confirmation flag (should fail)."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support firewall zones"}

    try:
        # Attempt to create zone without confirm=True
        await firewall_zones.create_firewall_zone(
            site_id=env.site_id,
            name=f"{TEST_PREFIX}TEST_ZONE",
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
async def test_create_and_delete_firewall_zone(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test create and delete firewall zone with automatic cleanup."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support firewall zones"}

    zone_id = None
    try:
        # Create test zone with minimal required fields
        # Note: API doesn't accept description field on creation
        result = await firewall_zones.create_firewall_zone(
            site_id=env.site_id,
            name=f"{TEST_PREFIX}ZONE_DELETE_ME",
            settings=settings,
            confirm=True,
        )

        zone_id = result.get("id") or result.get("_id")
        assert zone_id is not None, "Zone creation must return id or _id"
        assert result.get("name") == f"{TEST_PREFIX}ZONE_DELETE_ME", "Name must match"

        # Verify zone exists in list
        zones = await firewall_zones.list_firewall_zones(
            site_id=env.site_id,
            settings=settings,
        )
        assert any(
            z.get("id") == zone_id or z.get("_id") == zone_id for z in zones
        ), "Created zone must be in list"

        # Delete the zone
        delete_result = await firewall_zones.delete_firewall_zone(
            site_id=env.site_id,
            zone_id=zone_id,
            settings=settings,
            confirm=True,
        )

        assert delete_result.get("status") == "success", "Deletion must succeed"
        assert delete_result.get("zone_id") == zone_id, "Deleted ID must match"

        # Verify zone no longer exists
        zones_after = await firewall_zones.list_firewall_zones(
            site_id=env.site_id,
            settings=settings,
        )
        assert not any(
            z.get("id") == zone_id or z.get("_id") == zone_id for z in zones_after
        ), "Deleted zone must not be in list"

        # Clear zone_id since it was successfully deleted
        zone_id = None

        return {
            "status": "PASS",
            "message": "Created and deleted firewall zone successfully",
            "details": {"operation": "create -> verify -> delete -> verify"},
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}
    finally:
        # CRITICAL: Always cleanup, even on failure
        if zone_id:
            try:
                await firewall_zones.delete_firewall_zone(
                    site_id=env.site_id,
                    zone_id=zone_id,
                    settings=settings,
                    confirm=True,
                )
                print(f"Cleanup: Deleted test zone {zone_id}")
            except Exception as cleanup_err:
                print(f"WARNING: Failed to cleanup zone {zone_id}: {cleanup_err}")


@pytest.mark.integration
async def test_update_firewall_zone(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test update_firewall_zone with create-update-delete pattern."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support firewall zones"}

    zone_id = None
    try:
        # Create test zone
        created = await firewall_zones.create_firewall_zone(
            site_id=env.site_id,
            name=f"{TEST_PREFIX}UPDATE_TEST",
            settings=settings,
            confirm=True,
        )

        zone_id = created.get("id") or created.get("_id")
        assert zone_id is not None, "Zone creation must return id or _id"

        # Update the zone (name only - API doesn't support description on update either)
        updated = await firewall_zones.update_firewall_zone(
            site_id=env.site_id,
            firewall_zone_id=zone_id,
            settings=settings,
            name=f"{TEST_PREFIX}UPDATED_ZONE",
            confirm=True,
        )

        zone_id_updated = updated.get("id") or updated.get("_id")
        assert zone_id_updated == zone_id, "Updated zone ID must match"
        assert updated.get("name") == f"{TEST_PREFIX}UPDATED_ZONE", "Name must be updated"

        return {
            "status": "PASS",
            "message": "Updated firewall zone successfully",
            "details": {
                "original_name": f"{TEST_PREFIX}UPDATE_TEST",
                "updated_name": f"{TEST_PREFIX}UPDATED_ZONE",
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}
    finally:
        # CRITICAL: Always cleanup
        if zone_id:
            try:
                await firewall_zones.delete_firewall_zone(
                    site_id=env.site_id,
                    zone_id=zone_id,
                    settings=settings,
                    confirm=True,
                )
            except Exception as cleanup_err:
                print(f"WARNING: Failed to cleanup zone {zone_id}: {cleanup_err}")


@pytest.mark.integration
async def test_create_firewall_zone_dry_run(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test create_firewall_zone in dry-run mode."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support firewall zones"}

    try:
        result = await firewall_zones.create_firewall_zone(
            site_id=env.site_id,
            name=f"{TEST_PREFIX}DRY_RUN_TEST",
            settings=settings,
            confirm=True,
            dry_run=True,  # Should not create zone
        )

        assert result.get("dry_run") is True, "Must be dry-run mode"
        assert "payload" in result, "Should include payload"
        assert result["payload"].get("name") == f"{TEST_PREFIX}DRY_RUN_TEST"

        # Verify zone was NOT created
        zones = await firewall_zones.list_firewall_zones(
            site_id=env.site_id,
            settings=settings,
        )
        assert not any(
            z.get("name") == f"{TEST_PREFIX}DRY_RUN_TEST" for z in zones
        ), "Dry-run must not create zone"

        return {
            "status": "PASS",
            "message": "Dry-run validation successful (zone not created)",
            "details": {"dry_run": True},
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_get_zone_networks(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test get_zone_networks tool (requires existing zone)."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support firewall zones"}

    zone_id = None
    try:
        # Create a test zone first
        zone = await firewall_zones.create_firewall_zone(
            site_id=env.site_id,
            name=f"{TEST_PREFIX}NETWORKS_TEST",
            settings=settings,
            confirm=True,
        )

        zone_id = zone.get("id") or zone.get("_id")
        assert zone_id is not None, "Zone creation must return id or _id"

        # Get networks in the zone (should be empty for new zone)
        result = await firewall_zones.get_zone_networks(
            site_id=env.site_id,
            zone_id=zone_id,
            settings=settings,
        )

        assert isinstance(result, list), "Result must be a list"

        return {
            "status": "PASS",
            "message": f"Retrieved zone networks (count: {len(result)})",
            "details": {"zone_id": str(zone_id)[:8] + "...", "network_count": len(result)},
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}
    finally:
        # CRITICAL: Always cleanup
        if zone_id:
            try:
                await firewall_zones.delete_firewall_zone(
                    site_id=env.site_id,
                    zone_id=zone_id,
                    settings=settings,
                    confirm=True,
                )
            except Exception as cleanup_err:
                print(f"WARNING: Failed to cleanup zone {zone_id}: {cleanup_err}")


@pytest.mark.integration
async def test_delete_firewall_zone_dry_run(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test delete_firewall_zone in dry-run mode."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support firewall zones"}

    zone_id = None
    try:
        # Create a test zone
        zone = await firewall_zones.create_firewall_zone(
            site_id=env.site_id,
            name=f"{TEST_PREFIX}DRY_DELETE_TEST",
            settings=settings,
            confirm=True,
        )

        zone_id = zone.get("id") or zone.get("_id")
        assert zone_id is not None, "Zone creation must return id or _id"

        # Attempt dry-run deletion
        result = await firewall_zones.delete_firewall_zone(
            site_id=env.site_id,
            zone_id=zone_id,
            settings=settings,
            confirm=True,
            dry_run=True,  # Should not actually delete
        )

        assert result.get("dry_run") is True, "Must be dry-run mode"
        assert result.get("action") == "would_delete", "Should indicate planned deletion"

        # Verify zone still exists
        zones = await firewall_zones.list_firewall_zones(
            site_id=env.site_id,
            settings=settings,
        )
        assert any(
            z.get("id") == zone_id or z.get("_id") == zone_id for z in zones
        ), "Dry-run must not delete zone"

        return {
            "status": "PASS",
            "message": "Dry-run deletion validation successful (zone not deleted)",
            "details": {"dry_run": True},
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}
    finally:
        # CRITICAL: Always cleanup - actually delete the zone
        if zone_id:
            try:
                await firewall_zones.delete_firewall_zone(
                    site_id=env.site_id,
                    zone_id=zone_id,
                    settings=settings,
                    confirm=True,
                )
            except Exception as cleanup_err:
                print(f"WARNING: Failed to cleanup zone {zone_id}: {cleanup_err}")


def create_firewall_zones_suite() -> TestSuite:
    """Create the firewall zones test suite."""
    return TestSuite(
        name="firewall-zones",
        description="Firewall Zones Tools - list, create, update, delete zones with validation and cleanup",
        tests=[
            test_local_api_requirement,
            test_list_firewall_zones,
            test_create_firewall_zone_without_confirmation,
            test_create_and_delete_firewall_zone,
            test_update_firewall_zone,
            test_create_firewall_zone_dry_run,
            test_get_zone_networks,
            test_delete_firewall_zone_dry_run,
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

        suite = create_firewall_zones_suite()
        harness.register_suite(suite)

        # Parse environment filter
        env_filter = None
        if "--env" in sys.argv:
            idx = sys.argv.index("--env")
            if idx + 1 < len(sys.argv):
                env_filter = [sys.argv[idx + 1]]

        # Run suite
        await harness.run_suite("firewall-zones", environment_filter=env_filter)

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
