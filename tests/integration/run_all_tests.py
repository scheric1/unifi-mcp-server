#!/usr/bin/env python3
"""
UniFi MCP Server - Comprehensive Integration Test Runner

Runs all integration test suites across all configured environments.
Used for regression testing before releases.

Usage:
    # Run all tests on all environments
    python tests/integration/run_all_tests.py

    # Run tests on specific environment
    python tests/integration/run_all_tests.py --env unifi-lab

    # Run with verbose output
    python tests/integration/run_all_tests.py --verbose

    # Export results to JSON
    python tests/integration/run_all_tests.py --export results.json

    # Run specific suite
    python tests/integration/run_all_tests.py --suite topology

    # Dry run (list what would be tested)
    python tests/integration/run_all_tests.py --dry-run
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv

# Import all test suites
from tests.integration.test_client_ops_suite import create_client_ops_suite
from tests.integration.test_client_suite import create_client_suite
from tests.integration.test_cloud_suite import create_cloud_suite
from tests.integration.test_device_ops_suite import create_device_ops_suite
from tests.integration.test_device_suite import create_device_suite
from tests.integration.test_dpi_suite import create_dpi_suite
from tests.integration.test_firewall_suite import create_firewall_suite
from tests.integration.test_firewall_zones_suite import create_firewall_zones_suite
from tests.integration.test_harness import TestEnvironment, TestHarness
from tests.integration.test_network_suite import create_network_suite
from tests.integration.test_port_forwarding_suite import create_port_forwarding_suite
from tests.integration.test_topology_suite import create_topology_suite
from tests.integration.test_traffic_flows_suite import create_traffic_flows_suite


def discover_test_suites():
    """Discover and return all test suites."""
    suites = []

    # Week 1: Safe read-only test suites
    suites.append(create_device_suite())  # Device management (8 tests)
    suites.append(create_client_suite())  # Client management (8 tests)
    suites.append(create_network_suite())  # Network configuration (7 tests)
    suites.append(create_cloud_suite())  # Site management (10 tests)

    # Topology suite (existing)
    suites.append(create_topology_suite())  # Network topology (8 tests)

    # Week 2: Medium risk test suites
    suites.append(create_firewall_suite())  # Firewall management (9 tests)
    suites.append(create_port_forwarding_suite())  # Port forwarding (7 tests)
    suites.append(create_dpi_suite())  # DPI statistics (5 tests)

    # Week 3: High risk test suites
    suites.append(create_traffic_flows_suite())  # Traffic flow monitoring (11 tests)
    suites.append(create_firewall_zones_suite())  # Firewall zones (8 tests)

    # Week 4: Destructive operations test suites (DRY-RUN ONLY)
    suites.append(create_device_ops_suite())  # Device operations (5 tests)
    suites.append(create_client_ops_suite())  # Client operations (4 tests)

    return suites


def load_test_environments() -> list[TestEnvironment]:
    """Load test environments from .env file."""
    # Try to load from integration tests directory first
    integration_env = Path(__file__).parent / ".env"
    if integration_env.exists():
        load_dotenv(integration_env)
    else:
        # Fallback to project root .env
        load_dotenv()

    import os

    environments = []

    # Load unifi-lab environment
    lab_key = os.getenv("UNIFI_LAB_API_KEY") or os.getenv("UNIFI_API_KEY")
    lab_host = os.getenv("UNIFI_LAB_HOST") or os.getenv("UNIFI_LOCAL_HOST")
    if lab_key and lab_host:
        environments.append(
            TestEnvironment(
                name="unifi-lab",
                api_type="local",
                api_key=lab_key,
                local_host=lab_host,
                local_port=int(
                    os.getenv("UNIFI_LAB_PORT") or os.getenv("UNIFI_LOCAL_PORT") or "443"
                ),
                verify_ssl=(
                    os.getenv("UNIFI_LAB_VERIFY_SSL")
                    or os.getenv("UNIFI_LOCAL_VERIFY_SSL")
                    or "false"
                ).lower()
                == "true",
            )
        )

    # Load unifi-home environment
    home_key = os.getenv("UNIFI_HOME_API_KEY")
    home_host = os.getenv("UNIFI_HOME_HOST")
    if home_key and home_host:
        environments.append(
            TestEnvironment(
                name="unifi-home",
                api_type="local",
                api_key=home_key,
                local_host=home_host,
                local_port=int(os.getenv("UNIFI_HOME_PORT", "443")),
                verify_ssl=os.getenv("UNIFI_HOME_VERIFY_SSL", "false").lower() == "true",
            )
        )

    # Load cloud-v1 environment (lab site)
    cloud_v1_key = os.getenv("UNIFI_CLOUD_V1_API_KEY") or os.getenv("UNIFI_CLOUD_API_KEY")
    cloud_site_lab = os.getenv("UNIFI_CLOUD_SITE_LAB", "63be0605bc01d21891cef8df")
    if cloud_v1_key:
        environments.append(
            TestEnvironment(
                name="unifi-cloud-v1-lab",
                api_type="cloud-v1",
                api_key=cloud_v1_key,
                site_id=cloud_site_lab,
            )
        )

    # Load cloud-ea environment (lab site)
    cloud_ea_key = os.getenv("UNIFI_CLOUD_EA_API_KEY") or os.getenv("UNIFI_CLOUD_API_KEY")
    if cloud_ea_key:
        environments.append(
            TestEnvironment(
                name="unifi-cloud-ea-lab",
                api_type="cloud-ea",
                api_key=cloud_ea_key,
                site_id=cloud_site_lab,
            )
        )

    # Load cloud-v1 environment (home site)
    cloud_site_home = os.getenv("UNIFI_CLOUD_SITE_HOME", "68f9483dd8b48c07c614ff34")
    if cloud_v1_key:
        environments.append(
            TestEnvironment(
                name="unifi-cloud-v1-home",
                api_type="cloud-v1",
                api_key=cloud_v1_key,
                site_id=cloud_site_home,
            )
        )

    # Load cloud-ea environment (home site)
    if cloud_ea_key:
        environments.append(
            TestEnvironment(
                name="unifi-cloud-ea-home",
                api_type="cloud-ea",
                api_key=cloud_ea_key,
                site_id=cloud_site_home,
            )
        )

    return environments


def print_test_plan(harness: TestHarness, suite_filter: str | None = None):
    """Print what tests will be run (dry-run mode)."""
    print("\n" + "=" * 70)
    print("TEST PLAN (DRY RUN)")
    print("=" * 70)

    print(f"\nEnvironments ({len(harness.environments)}):")
    for env in harness.environments:
        print(f"  - {env.name} ({env.api_type})")

    print("\nTest Suites:")
    total_tests = 0
    for suite_name, suite in harness.test_suites.items():
        if suite_filter and suite_name != suite_filter:
            continue
        test_count = len(suite.tests)
        total_tests += test_count
        print(f"  - {suite_name}: {test_count} tests")
        if suite.description:
            print(f"    {suite.description}")

    total_executions = total_tests * len(harness.environments)
    print(f"\nTotal Test Executions: {total_executions}")
    print("=" * 70 + "\n")


async def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description="UniFi MCP Server Integration Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--env",
        help="Run tests only on specific environment (unifi-lab, unifi-home, unifi-cloud)",
    )
    parser.add_argument(
        "--suite",
        help="Run specific test suite only",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--export",
        metavar="FILE",
        help="Export results to JSON file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what tests would be run without executing them",
    )

    args = parser.parse_args()

    # Load environments
    environments = load_test_environments()

    if not environments:
        print("❌ No test environments configured!")
        print("Please create tests/integration/.env or .env with environment configuration.")
        print("See tests/integration/.env.example for template.")
        sys.exit(1)

    # Filter environments
    if args.env:
        environments = [e for e in environments if e.name == args.env]
        if not environments:
            print(f"❌ Environment '{args.env}' not found!")
            sys.exit(1)

    # Create harness
    harness = TestHarness(environments=environments)
    harness.verbose = args.verbose

    # Discover and register test suites
    suites = discover_test_suites()
    for suite in suites:
        harness.register_suite(suite)

    # Dry run mode
    if args.dry_run:
        print_test_plan(harness, args.suite)
        return

    # Print header
    print("\n" + "=" * 70)
    print("UniFi MCP Server - Integration Test Run")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Run tests
    start_time = datetime.now()

    if args.suite:
        # Run specific suite
        await harness.run_suite(args.suite, environment_filter=[args.env] if args.env else None)
    else:
        # Run all suites
        await harness.run_all(environment_filter=[args.env] if args.env else None)

    end_time = datetime.now()

    # Print summary
    harness.print_summary()

    print(f"Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {(end_time - start_time).total_seconds():.2f}s")

    # Export results if requested
    if args.export:
        output_file = Path(args.export)
        harness.export_results(output_file)

    # Exit with error code if any tests failed
    failed_count = sum(1 for r in harness.results if r.status.value in ["FAIL", "ERROR"])
    sys.exit(1 if failed_count > 0 else 0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test run interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Test run failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
