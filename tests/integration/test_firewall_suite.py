#!/usr/bin/env python3
"""
Firewall Management Integration Test Suite

Tests all firewall-related MCP tools against real UniFi environments.
Implements create-test-delete pattern with automatic cleanup.
"""

from typing import Any

import pytest

from src.tools import firewall
from src.utils import ResourceNotFoundError, ValidationError
from tests.integration.test_harness import TestEnvironment, TestSuite

# Test resource prefix
TEST_PREFIX = "TEST_INTEGRATION_"


@pytest.mark.integration
async def test_list_firewall_rules(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test list_firewall_rules tool."""
    # Skip on cloud APIs - firewall management is local only
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {
            "status": "SKIP",
            "message": "Cloud APIs do not support firewall management (local only)",
        }

    try:
        result = await firewall.list_firewall_rules(
            site_id=env.site_id,
            settings=settings,
        )

        # Validate response structure
        assert isinstance(result, list), "Result must be a list"

        if not result:
            return {
                "status": "SKIP",
                "message": "No firewall rules found (site may be unconfigured)",
            }

        # Validate rule structure
        rule = result[0]
        assert "_id" in rule, "Rule must have _id"
        assert "name" in rule, "Rule must have name"
        assert "action" in rule, "Rule must have action"

        return {
            "status": "PASS",
            "message": f"Listed {len(result)} firewall rules",
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
async def test_list_firewall_rules_pagination(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test list_firewall_rules with pagination."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support firewall management"}

    try:
        # Get all rules
        all_rules = await firewall.list_firewall_rules(
            site_id=env.site_id,
            settings=settings,
        )

        if not all_rules:
            return {"status": "SKIP", "message": "No rules found for pagination test"}

        # Test with limit
        limited = await firewall.list_firewall_rules(
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
async def test_create_firewall_rule_without_confirmation(
    settings, env: TestEnvironment
) -> dict[str, Any]:
    """Test create_firewall_rule without confirmation flag (should fail)."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support firewall management"}

    try:
        # Attempt to create rule without confirm=True
        await firewall.create_firewall_rule(
            site_id=env.site_id,
            name=f"{TEST_PREFIX}TEST_RULE",
            action="drop",
            settings=settings,
            protocol="tcp",
            port=9999,
            enabled=False,
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
async def test_create_and_delete_firewall_rule(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test create and delete firewall rule with automatic cleanup."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support firewall management"}

    rule_id = None
    try:
        # Create test rule with minimal required fields
        # Note: UniFi API requires specific field combinations
        result = await firewall.create_firewall_rule(
            site_id=env.site_id,
            name=f"{TEST_PREFIX}RULE_DELETE_ME",
            action="drop",
            settings=settings,
            source="192.0.2.0/24",  # TEST-NET-1 (RFC 5737) - test source
            protocol="all",  # Use "all" protocol for simpler rule
            enabled=False,  # Keep disabled for safety
            ruleset="WAN_LOCAL",  # Use WAN_LOCAL ruleset
            rule_index=20001,  # Use index range that works with this ruleset
            confirm=True,
        )

        rule_id = result.get("_id")
        assert rule_id is not None, "Rule creation must return _id"
        assert result.get("name") == f"{TEST_PREFIX}RULE_DELETE_ME", "Name must match"
        assert result.get("action") == "drop", "Action must match"

        # Verify rule exists in list
        rules = await firewall.list_firewall_rules(
            site_id=env.site_id,
            settings=settings,
        )
        assert any(r.get("_id") == rule_id for r in rules), "Created rule must be in list"

        # Delete the rule
        delete_result = await firewall.delete_firewall_rule(
            site_id=env.site_id,
            rule_id=rule_id,
            settings=settings,
            confirm=True,
        )

        assert delete_result.get("success") is True, "Deletion must succeed"
        assert delete_result.get("deleted_rule_id") == rule_id, "Deleted ID must match"

        # Verify rule no longer exists
        rules_after = await firewall.list_firewall_rules(
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
            "message": "Created and deleted firewall rule successfully",
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
                await firewall.delete_firewall_rule(
                    site_id=env.site_id,
                    rule_id=rule_id,
                    settings=settings,
                    confirm=True,
                )
                print(f"Cleanup: Deleted test rule {rule_id}")
            except Exception as cleanup_err:
                print(f"WARNING: Failed to cleanup rule {rule_id}: {cleanup_err}")


@pytest.mark.integration
async def test_update_firewall_rule(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test update_firewall_rule with create-update-delete pattern."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support firewall management"}

    rule_id = None
    try:
        # Create test rule
        created = await firewall.create_firewall_rule(
            site_id=env.site_id,
            name=f"{TEST_PREFIX}UPDATE_TEST",
            action="accept",
            settings=settings,
            source="192.0.2.0/24",  # TEST-NET-1
            protocol="all",  # Use "all" protocol
            enabled=False,
            ruleset="WAN_LOCAL",  # Use WAN_LOCAL ruleset
            rule_index=20002,  # Use index range that works with this ruleset
            confirm=True,
        )

        rule_id = created.get("_id")
        assert rule_id is not None, "Rule creation must return _id"

        # Update the rule
        updated = await firewall.update_firewall_rule(
            site_id=env.site_id,
            rule_id=rule_id,
            settings=settings,
            name=f"{TEST_PREFIX}UPDATED_RULE",
            action="drop",
            confirm=True,
        )

        assert updated.get("_id") == rule_id, "Updated rule ID must match"
        assert updated.get("name") == f"{TEST_PREFIX}UPDATED_RULE", "Name must be updated"
        assert updated.get("action") == "drop", "Action must be updated"

        return {
            "status": "PASS",
            "message": "Updated firewall rule successfully",
            "details": {
                "original_name": f"{TEST_PREFIX}UPDATE_TEST",
                "updated_name": f"{TEST_PREFIX}UPDATED_RULE",
            },
        }

    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}
    finally:
        # CRITICAL: Always cleanup
        if rule_id:
            try:
                await firewall.delete_firewall_rule(
                    site_id=env.site_id,
                    rule_id=rule_id,
                    settings=settings,
                    confirm=True,
                )
            except Exception as cleanup_err:
                print(f"WARNING: Failed to cleanup rule {rule_id}: {cleanup_err}")


@pytest.mark.integration
async def test_delete_firewall_rule_missing(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test delete_firewall_rule with non-existent rule ID (expect error)."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support firewall management"}

    try:
        fake_id = "000000000000000000000000"  # Non-existent ObjectId format

        await firewall.delete_firewall_rule(
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
async def test_create_firewall_rule_dry_run(settings, env: TestEnvironment) -> dict[str, Any]:
    """Test create_firewall_rule in dry-run mode."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support firewall management"}

    try:
        result = await firewall.create_firewall_rule(
            site_id=env.site_id,
            name=f"{TEST_PREFIX}DRY_RUN_TEST",
            action="drop",
            settings=settings,
            protocol="tcp",
            port=9999,
            enabled=False,
            confirm=True,
            dry_run=True,  # Should not create rule
        )

        assert result.get("dry_run") is True, "Must be dry-run mode"
        assert "would_create" in result, "Should indicate planned action"
        assert result["would_create"].get("name") == f"{TEST_PREFIX}DRY_RUN_TEST"

        # Verify rule was NOT created
        rules = await firewall.list_firewall_rules(
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
async def test_create_firewall_rule_invalid_action(
    settings, env: TestEnvironment
) -> dict[str, Any]:
    """Test create_firewall_rule with invalid action (should fail validation)."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support firewall management"}

    try:
        await firewall.create_firewall_rule(
            site_id=env.site_id,
            name=f"{TEST_PREFIX}INVALID_ACTION",
            action="invalid_action",  # Invalid action
            settings=settings,
            confirm=True,
        )

        # If we get here, validation failed
        return {
            "status": "FAIL",
            "message": "Expected ValueError for invalid action but got result",
        }

    except ValueError as e:
        # Expected validation error
        if "Invalid action" in str(e):
            return {
                "status": "PASS",
                "message": "Correctly raised ValueError for invalid action",
            }
        return {"status": "FAIL", "message": f"Unexpected ValueError: {str(e)}"}
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Unexpected error type: {type(e).__name__}: {str(e)}",
        }


@pytest.mark.integration
async def test_create_firewall_rule_invalid_protocol(
    settings, env: TestEnvironment
) -> dict[str, Any]:
    """Test create_firewall_rule with invalid protocol (should fail validation)."""
    if env.api_type in ["cloud-v1", "cloud-ea"]:
        return {"status": "SKIP", "message": "Cloud APIs do not support firewall management"}

    try:
        await firewall.create_firewall_rule(
            site_id=env.site_id,
            name=f"{TEST_PREFIX}INVALID_PROTOCOL",
            action="drop",
            settings=settings,
            protocol="invalid_protocol",  # Invalid protocol
            confirm=True,
        )

        # If we get here, validation failed
        return {
            "status": "FAIL",
            "message": "Expected ValueError for invalid protocol but got result",
        }

    except ValueError as e:
        # Expected validation error
        if "Invalid protocol" in str(e):
            return {
                "status": "PASS",
                "message": "Correctly raised ValueError for invalid protocol",
            }
        return {"status": "FAIL", "message": f"Unexpected ValueError: {str(e)}"}
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Unexpected error type: {type(e).__name__}: {str(e)}",
        }


def create_firewall_suite() -> TestSuite:
    """Create the firewall management test suite."""
    return TestSuite(
        name="firewall",
        description="Firewall Management Tools - list, create, update, delete rules with validation and cleanup",
        tests=[
            test_list_firewall_rules,
            test_list_firewall_rules_pagination,
            test_create_firewall_rule_without_confirmation,
            test_create_and_delete_firewall_rule,
            test_update_firewall_rule,
            test_delete_firewall_rule_missing,
            test_create_firewall_rule_dry_run,
            test_create_firewall_rule_invalid_action,
            test_create_firewall_rule_invalid_protocol,
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

        suite = create_firewall_suite()
        harness.register_suite(suite)

        # Parse environment filter
        env_filter = None
        if "--env" in sys.argv:
            idx = sys.argv.index("--env")
            if idx + 1 < len(sys.argv):
                env_filter = [sys.argv[idx + 1]]

        # Run suite
        await harness.run_suite("firewall", environment_filter=env_filter)

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
