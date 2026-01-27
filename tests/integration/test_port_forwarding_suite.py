#!/usr/bin/env python3
"""
Port Forwarding Integration Test Suite

Tests all port forwarding MCP tools against real UniFi environments.
Uses high-numbered test ports (>50000) for safety.
"""

from typing import Any

import pytest

from src.tools import port_forwarding
from src.utils import ResourceNotFoundError, ValidationError
from tests.integration.test_harness import TestEnvironment, TestSuite

# Test resource prefix and safe test port
TEST_PREFIX = "TEST_INTEGRATION_"
TEST_PORT = 59999  # High-numbered port for safety


@pytest.mark.integration
async def test_list_port_forwards(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test list_port_forwards tool."""
    # Skip on cloud APIs - port forwarding is local only
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {
            "status": "SKIP",
            "message": "Cloud APIs do not support port forwarding (local only)",
        }

    try:
        result = await port_forwarding.list_port_forwards(
            site_id=env.site_id,
            settings=settings,
        )

        # Validate response structure
        assert isinstance(result, list), "Result must be a list"

        if not result:
            return {
                "status": "SKIP",
                "message": "No port forwarding rules found (may be unconfigured)",
            }

        # Validate rule structure
        rule = result[0]
        assert "_id" in rule, "Rule must have _id"
        assert "name" in rule, "Rule must have name"

        return {
            "status": "PASS",
            "message": f"Listed {len(result)} port forwarding rules",
            "details": {
                "count": len(result),
                "first_rule": rule.get("name", "unnamed"),
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_list_port_forwards_pagination(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test list_port_forwards with pagination."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support port forwarding"}

    try:
        # Get all rules
        all_rules = await port_forwarding.list_port_forwards(
            site_id=env.site_id,
            settings=settings,
        )

        if not all_rules:
            return {"status": "SKIP", "message": "No rules found for pagination test"}

        # Test with limit
        limited = await port_forwarding.list_port_forwards(
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
                "total_count": len(all_rules),
                "limited_count": len(limited),
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_create_port_forward_without_confirmation(
    settings, env: TestEnvironment
) -> dict[str, Any]:
    """Test create_port_forward without confirmation flag (should fail)."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support port forwarding"}

    try:
        # Attempt to create rule without confirm=True
        await port_forwarding.create_port_forward(
            site_id=env.site_id,
            name=f"{TEST_PREFIX}TEST_FORWARD",
            dst_port=TEST_PORT,
            fwd_ip="192.0.2.100",  # TEST-NET-1 (RFC 5737)
            fwd_port=8080,
            settings=settings,
            confirm=False,  # Should raise error
        )

        # If we get here, confirmation check failed
        return {
            "status": "FAIL",
            "message": "Expected ConfirmationRequiredError but got result",
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


@pytest.mark.integration
async def test_create_and_delete_port_forward(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test create and delete port forward with automatic cleanup."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support port forwarding"}

    rule_id = None
    try:
        # Create test port forward
        result = await port_forwarding.create_port_forward(
            site_id=env.site_id,
            name=f"{TEST_PREFIX}FORWARD_DELETE_ME",
            dst_port=TEST_PORT,
            fwd_ip="192.0.2.100",  # TEST-NET-1 (RFC 5737)
            fwd_port=8080,
            settings=settings,
            protocol="tcp",
            enabled=False,  # Keep disabled for safety
            confirm=True,
        )

        rule_id = result.get("_id")
        assert rule_id is not None, "Rule creation must return _id"
        assert result.get("name") == f"{TEST_PREFIX}FORWARD_DELETE_ME", "Name must match"

        # Verify rule exists in list
        rules = await port_forwarding.list_port_forwards(
            site_id=env.site_id,
            settings=settings,
        )
        assert any(r.get("_id") == rule_id for r in rules), "Created rule must be in list"

        # Delete the rule
        delete_result = await port_forwarding.delete_port_forward(
            site_id=env.site_id,
            rule_id=rule_id,
            settings=settings,
            confirm=True,
        )

        assert delete_result.get("success") is True, "Deletion must succeed"
        assert delete_result.get("deleted_rule_id") == rule_id, "Deleted ID must match"

        # Verify rule no longer exists
        rules_after = await port_forwarding.list_port_forwards(
            site_id=env.site_id,
            settings=settings,
        )
        assert not any(
            r.get("_id") == rule_id for r in rules_after
        ), "Deleted rule must not be in list"

        # Clear rule_id since it was successfully deleted
        rule_id = None

        return {
            "status": "PASS",
            "message": "Created and deleted port forward successfully",
            "details": {"operation": "create -> verify -> delete -> verify"},
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}
    finally:
        # CRITICAL: Always cleanup, even on failure
        if rule_id:
            try:
                await port_forwarding.delete_port_forward(
                    site_id=env.site_id,
                    rule_id=rule_id,
                    settings=settings,
                    confirm=True,
                )
                print(f"Cleanup: Deleted test port forward {rule_id}")
            except Exception as cleanup_err:
                print(f"WARNING: Failed to cleanup port forward {rule_id}: {cleanup_err}")


@pytest.mark.integration
async def test_delete_port_forward_missing(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test delete_port_forward with non-existent rule ID (expect error)."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support port forwarding"}

    try:
        fake_id = "000000000000000000000000"  # Non-existent ObjectId format

        await port_forwarding.delete_port_forward(
            site_id=env.site_id,
            rule_id=fake_id,
            settings=settings,
            confirm=True,
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
            "message": "Correctly raised ResourceNotFoundError for missing rule",
        }
    except Exception as e:
        # Unexpected error type
        return {
            "status": "ERROR",
            "message": f"Unexpected error type: {type(e).__name__}: {str(e)}",
        }


@pytest.mark.integration
async def test_create_port_forward_dry_run(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test create_port_forward in dry-run mode."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support port forwarding"}

    try:
        result = await port_forwarding.create_port_forward(
            site_id=env.site_id,
            name=f"{TEST_PREFIX}DRY_RUN_TEST",
            dst_port=TEST_PORT,
            fwd_ip="192.0.2.100",
            fwd_port=8080,
            settings=settings,
            confirm=True,
            dry_run=True,  # Should not create rule
        )

        assert result.get("dry_run") is True, "Must be dry-run mode"
        assert "would_create" in result, "Should indicate planned action"
        assert result["would_create"].get("name") == f"{TEST_PREFIX}DRY_RUN_TEST"

        # Verify rule was NOT created
        rules = await port_forwarding.list_port_forwards(
            site_id=env.site_id,
            settings=settings,
        )
        assert not any(
            r.get("name") == f"{TEST_PREFIX}DRY_RUN_TEST" for r in rules
        ), "Dry-run must not create rule"

        return {
            "status": "PASS",
            "message": "Dry-run validation successful (rule not created)",
            "details": {"dry_run": True},
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


@pytest.mark.integration
async def test_create_port_forward_invalid_ip(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test create_port_forward with invalid IP address (should fail validation)."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support port forwarding"}

    try:
        await port_forwarding.create_port_forward(
            site_id=env.site_id,
            name=f"{TEST_PREFIX}INVALID_IP",
            dst_port=TEST_PORT,
            fwd_ip="invalid.ip.address",  # Invalid IP
            fwd_port=8080,
            settings=settings,
            confirm=True,
        )

        # If we get here, validation failed
        return {
            "status": "FAIL",
            "message": "Expected ValidationError for invalid IP but got result",
        }

    except ValidationError as e:
        # Expected validation error
        if "IP address" in str(e) or "Invalid" in str(e):
            return {
                "status": "PASS",
                "message": "Correctly raised ValidationError for invalid IP",
            }
        return {"status": "FAIL", "message": f"Unexpected ValidationError: {str(e)}"}
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Unexpected error type: {type(e).__name__}: {str(e)}",
        }


def create_port_forwarding_suite() -> TestSuite:
    """Create the port forwarding test suite."""
    return TestSuite(
        name="port-forwarding",
        description="Port Forwarding Tools - list, create, delete rules with validation and cleanup",
        tests=[
            test_list_port_forwards,
            test_list_port_forwards_pagination,
            test_create_port_forward_without_confirmation,
            test_create_and_delete_port_forward,
            test_delete_port_forward_missing,
            test_create_port_forward_dry_run,
            test_create_port_forward_invalid_ip,
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

        suite = create_port_forwarding_suite()
        harness.register_suite(suite)

        # Parse environment filter
        env_filter = None
        if "--env" in sys.argv:
            idx = sys.argv.index("--env")
            if idx + 1 < len(sys.argv):
                env_filter = [sys.argv[idx + 1]]

        # Run suite
        await harness.run_suite("port-forwarding", environment_filter=env_filter)

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
