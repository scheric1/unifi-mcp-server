"""Cloud API Integration Test Suite.

Tests basic operations that are supported by UniFi Cloud APIs.
"""

from typing import Any, Dict

from tests.integration.test_harness import TestEnvironment, TestSuite


async def test_list_sites(settings, env: TestEnvironment) -> Dict[str, Any]:
    """Test listing sites via cloud API."""
    try:
        from src.tools.sites import list_sites

        result = await list_sites(settings)
        assert isinstance(result, list), "Should return a list of sites"
        assert len(result) > 0, "Should have at least one site"

        # Verify site structure
        site = result[0]
        assert "id" in site or "_id" in site, "Site should have an ID"
        assert "name" in site, "Site should have a name"

        return {
            "status": "PASS",
            "message": f"Retrieved {len(result)} site(s)",
            "details": {"site_count": len(result), "first_site": site.get("name")},
        }
    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


async def test_get_site_details_cloud(settings, env: TestEnvironment) -> Dict[str, Any]:
    """Test retrieving site details."""
    try:
        from src.tools.sites import get_site_details, list_sites

        # Get first site
        sites = await list_sites(settings)
        assert len(sites) > 0, "Need at least one site for testing"

        site_id = sites[0].get("id") or sites[0].get("_id")
        result = await get_site_details(site_id, settings)

        assert isinstance(result, dict), "Should return site details"
        assert "name" in result or "desc" in result, "Site should have a name or description"

        site_name = result.get("name") or result.get("desc") or "Unknown"

        return {
            "status": "PASS",
            "message": f"Retrieved details for site: {site_name}",
            "details": {"site_id": site_id[:12] + "...", "has_desc": "desc" in result},
        }
    except AssertionError as e:
        return {"status": "FAIL", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


async def test_get_site_statistics(settings, env: TestEnvironment) -> Dict[str, Any]:
    """Test retrieving site statistics (cloud API)."""
    try:
        from src.tools.sites import get_site_statistics, list_sites

        # Get first site
        sites = await list_sites(settings)
        assert len(sites) > 0, "Need at least one site for testing"

        site_id = sites[0].get("id") or sites[0].get("_id")
        result = await get_site_statistics(site_id, settings)

        assert isinstance(result, dict), "Should return statistics dictionary"

        # Count how many stat fields are present
        stat_fields = [
            k
            for k in result.keys()
            if isinstance(result[k], (int, float)) and k not in ["_id", "id"]
        ]

        return {
            "status": "PASS",
            "message": f"Retrieved site statistics with {len(stat_fields)} metrics",
            "details": {
                "stat_fields": len(stat_fields),
                "has_stats": len(stat_fields) > 0,
            },
        }
    except Exception as e:
        error_msg = str(e).lower()
        # Cloud APIs may not support detailed statistics
        if "not supported" in error_msg or "not found" in error_msg or "404" in error_msg:
            return {
                "status": "SKIP",
                "message": "Site statistics not supported on this API (expected for cloud)",
            }
        return {"status": "ERROR", "message": f"{type(e).__name__}: {str(e)}"}


def create_cloud_suite() -> TestSuite:
    """Create cloud API test suite."""
    suite = TestSuite(
        name="cloud-api",
        description="Cloud API Basic Operations - sites and authentication",
        tests=[
            test_list_sites,
            test_get_site_details_cloud,
            test_get_site_statistics,
        ],
    )
    return suite
