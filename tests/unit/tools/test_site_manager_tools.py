"""Tests for Site Manager tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tools.site_manager import (
    get_cross_site_statistics,
    get_internet_health,
    get_site_health_summary,
    list_all_sites_aggregated,
    list_vantage_points,
)


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = MagicMock()
    settings.log_level = "INFO"
    settings.site_manager_enabled = True
    settings.api_key = "test-key"
    settings.request_timeout = 30.0
    settings.get_headers = MagicMock(return_value={"X-API-Key": "test-key"})
    return settings


@pytest.fixture
def mock_settings_disabled():
    """Create mock settings with site manager disabled."""
    settings = MagicMock()
    settings.log_level = "INFO"
    settings.site_manager_enabled = False
    return settings


# =============================================================================
# Task 4.1: Test list_all_sites_aggregated
# =============================================================================


@pytest.mark.asyncio
async def test_list_all_sites_aggregated_success(mock_settings):
    """Test successful retrieval of aggregated sites list."""
    mock_response = {
        "data": [
            {
                "site_id": "site-1",
                "name": "Main Office",
                "devices": 5,
                "clients": 25,
            },
            {
                "site_id": "site-2",
                "name": "Branch Office",
                "devices": 3,
                "clients": 10,
            },
        ]
    }

    with patch("src.tools.site_manager.SiteManagerClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.list_sites = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await list_all_sites_aggregated(mock_settings)

        assert len(result) == 2
        assert result[0]["site_id"] == "site-1"
        assert result[0]["name"] == "Main Office"
        assert result[1]["site_id"] == "site-2"
        mock_client.list_sites.assert_called_once()


@pytest.mark.asyncio
async def test_list_all_sites_aggregated_empty(mock_settings):
    """Test retrieval when no sites exist."""
    mock_response = {"data": []}

    with patch("src.tools.site_manager.SiteManagerClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.list_sites = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await list_all_sites_aggregated(mock_settings)

        assert result == []
        mock_client.list_sites.assert_called_once()


@pytest.mark.asyncio
async def test_list_all_sites_aggregated_disabled(mock_settings_disabled):
    """Test that function raises when site manager is disabled."""
    with pytest.raises(ValueError) as excinfo:
        await list_all_sites_aggregated(mock_settings_disabled)

    assert "Site Manager API is not enabled" in str(excinfo.value)


@pytest.mark.asyncio
async def test_list_all_sites_aggregated_alternate_response_format(mock_settings):
    """Test handling of 'sites' key instead of 'data'."""
    mock_response = {
        "sites": [
            {
                "site_id": "site-1",
                "name": "Office",
            }
        ]
    }

    with patch("src.tools.site_manager.SiteManagerClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.list_sites = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await list_all_sites_aggregated(mock_settings)

        assert len(result) == 1
        assert result[0]["site_id"] == "site-1"


# =============================================================================
# Task 4.2: Test get_internet_health
# =============================================================================


@pytest.mark.asyncio
async def test_get_internet_health_all_sites(mock_settings):
    """Test internet health retrieval for all sites (no site_id)."""
    mock_response = {
        "data": {
            "latency_ms": 25.5,
            "packet_loss_percent": 0.1,
            "jitter_ms": 2.3,
            "bandwidth_up_mbps": 100.0,
            "bandwidth_down_mbps": 500.0,
            "status": "healthy",
            "last_tested": "2026-01-05T00:00:00Z",
        }
    }

    with patch("src.tools.site_manager.SiteManagerClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get_internet_health = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await get_internet_health(mock_settings)

        assert result["status"] == "healthy"
        assert result["latency_ms"] == 25.5
        assert result["bandwidth_down_mbps"] == 500.0
        mock_client.get_internet_health.assert_called_once_with(None)


@pytest.mark.asyncio
async def test_get_internet_health_specific_site(mock_settings):
    """Test internet health retrieval for a specific site."""
    mock_response = {
        "data": {
            "site_id": "site-1",
            "latency_ms": 15.0,
            "packet_loss_percent": 0.0,
            "jitter_ms": 1.0,
            "bandwidth_up_mbps": 50.0,
            "bandwidth_down_mbps": 200.0,
            "status": "healthy",
            "last_tested": "2026-01-05T00:00:00Z",
        }
    }

    with patch("src.tools.site_manager.SiteManagerClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get_internet_health = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await get_internet_health(mock_settings, site_id="site-1")

        assert result["site_id"] == "site-1"
        assert result["status"] == "healthy"
        mock_client.get_internet_health.assert_called_once_with("site-1")


@pytest.mark.asyncio
async def test_get_internet_health_degraded(mock_settings):
    """Test internet health when connection is degraded."""
    mock_response = {
        "data": {
            "latency_ms": 150.0,
            "packet_loss_percent": 5.5,
            "jitter_ms": 25.0,
            "bandwidth_up_mbps": 10.0,
            "bandwidth_down_mbps": 50.0,
            "status": "degraded",
            "last_tested": "2026-01-05T00:00:00Z",
        }
    }

    with patch("src.tools.site_manager.SiteManagerClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get_internet_health = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await get_internet_health(mock_settings)

        assert result["status"] == "degraded"
        assert result["packet_loss_percent"] == 5.5


@pytest.mark.asyncio
async def test_get_internet_health_disabled(mock_settings_disabled):
    """Test that function raises when site manager is disabled."""
    with pytest.raises(ValueError) as excinfo:
        await get_internet_health(mock_settings_disabled)

    assert "Site Manager API is not enabled" in str(excinfo.value)


# =============================================================================
# Task 4.3: Test get_site_health_summary and get_cross_site_statistics
# =============================================================================


@pytest.mark.asyncio
async def test_get_site_health_summary_specific_site(mock_settings):
    """Test health summary for a specific site."""
    mock_response = {
        "site_id": "site-1",
        "site_name": "Main Office",
        "status": "healthy",
        "devices_online": 5,
        "devices_total": 5,
        "clients_active": 25,
        "uptime_percentage": 99.9,
        "last_updated": "2026-01-05T00:00:00Z",
    }

    with patch("src.tools.site_manager.SiteManagerClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get_site_health = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await get_site_health_summary(mock_settings, site_id="site-1")

        assert result["site_id"] == "site-1"
        assert result["status"] == "healthy"
        assert result["devices_online"] == 5
        mock_client.get_site_health.assert_called_once_with("site-1")


@pytest.mark.asyncio
async def test_get_site_health_summary_all_sites(mock_settings):
    """Test health summary for all sites."""
    mock_response = {
        "sites": [
            {
                "site_id": "site-1",
                "site_name": "Main Office",
                "status": "healthy",
                "devices_online": 5,
                "devices_total": 5,
                "clients_active": 25,
                "uptime_percentage": 99.9,
                "last_updated": "2026-01-05T00:00:00Z",
            },
            {
                "site_id": "site-2",
                "site_name": "Branch Office",
                "status": "degraded",
                "devices_online": 2,
                "devices_total": 3,
                "clients_active": 10,
                "uptime_percentage": 95.0,
                "last_updated": "2026-01-05T00:00:00Z",
            },
        ]
    }

    with patch("src.tools.site_manager.SiteManagerClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get_site_health = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await get_site_health_summary(mock_settings)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["site_id"] == "site-1"
        assert result[1]["status"] == "degraded"
        mock_client.get_site_health.assert_called_once_with(None)


@pytest.mark.asyncio
async def test_get_site_health_summary_disabled(mock_settings_disabled):
    """Test that function raises when site manager is disabled."""
    with pytest.raises(ValueError) as excinfo:
        await get_site_health_summary(mock_settings_disabled)

    assert "Site Manager API is not enabled" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_cross_site_statistics_success(mock_settings):
    """Test cross-site statistics aggregation."""
    mock_sites_response = {
        "data": [
            {"site_id": "site-1", "name": "Site 1"},
            {"site_id": "site-2", "name": "Site 2"},
            {"site_id": "site-3", "name": "Site 3"},
        ]
    }
    mock_health_response = {
        "data": [
            {
                "site_id": "site-1",
                "site_name": "Site 1",
                "status": "healthy",
                "devices_online": 5,
                "devices_total": 5,
                "clients_active": 25,
                "uptime_percentage": 99.9,
                "last_updated": "2026-01-05T00:00:00Z",
            },
            {
                "site_id": "site-2",
                "site_name": "Site 2",
                "status": "degraded",
                "devices_online": 2,
                "devices_total": 3,
                "clients_active": 10,
                "uptime_percentage": 95.0,
                "last_updated": "2026-01-05T00:00:00Z",
            },
            {
                "site_id": "site-3",
                "site_name": "Site 3",
                "status": "down",
                "devices_online": 0,
                "devices_total": 2,
                "clients_active": 0,
                "uptime_percentage": 0.0,
                "last_updated": "2026-01-05T00:00:00Z",
            },
        ]
    }

    with patch("src.tools.site_manager.SiteManagerClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.list_sites = AsyncMock(return_value=mock_sites_response)
        mock_client.get_site_health = AsyncMock(return_value=mock_health_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await get_cross_site_statistics(mock_settings)

        assert result["total_sites"] == 3
        assert result["sites_healthy"] == 1
        assert result["sites_degraded"] == 1
        assert result["sites_down"] == 1
        assert result["total_devices"] == 10  # 5 + 3 + 2
        assert result["devices_online"] == 7  # 5 + 2 + 0
        assert result["total_clients"] == 35  # 25 + 10 + 0
        assert len(result["site_summaries"]) == 3


@pytest.mark.asyncio
async def test_get_cross_site_statistics_empty(mock_settings):
    """Test cross-site statistics with no sites."""
    mock_sites_response = {"data": []}
    mock_health_response = {"data": []}

    with patch("src.tools.site_manager.SiteManagerClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.list_sites = AsyncMock(return_value=mock_sites_response)
        mock_client.get_site_health = AsyncMock(return_value=mock_health_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await get_cross_site_statistics(mock_settings)

        assert result["total_sites"] == 0
        assert result["sites_healthy"] == 0
        assert result["total_devices"] == 0
        assert len(result["site_summaries"]) == 0


@pytest.mark.asyncio
async def test_get_cross_site_statistics_disabled(mock_settings_disabled):
    """Test that function raises when site manager is disabled."""
    with pytest.raises(ValueError) as excinfo:
        await get_cross_site_statistics(mock_settings_disabled)

    assert "Site Manager API is not enabled" in str(excinfo.value)


# =============================================================================
# Task 4.4: Test list_vantage_points
# =============================================================================


@pytest.mark.asyncio
async def test_list_vantage_points_success(mock_settings):
    """Test successful retrieval of Vantage Points."""
    mock_response = {
        "vantage_points": [
            {
                "vantage_point_id": "vp-1",
                "name": "New York Office",
                "location": "New York, NY",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "status": "active",
                "site_ids": ["site-1", "site-2"],
            },
            {
                "vantage_point_id": "vp-2",
                "name": "London Office",
                "location": "London, UK",
                "latitude": 51.5074,
                "longitude": -0.1278,
                "status": "active",
                "site_ids": ["site-3"],
            },
        ]
    }

    with patch("src.tools.site_manager.SiteManagerClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.list_vantage_points = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await list_vantage_points(mock_settings)

        assert len(result) == 2
        assert result[0]["vantage_point_id"] == "vp-1"
        assert result[0]["name"] == "New York Office"
        assert result[0]["status"] == "active"
        assert len(result[0]["site_ids"]) == 2
        mock_client.list_vantage_points.assert_called_once()


@pytest.mark.asyncio
async def test_list_vantage_points_empty(mock_settings):
    """Test retrieval when no Vantage Points exist."""
    mock_response = {"vantage_points": []}

    with patch("src.tools.site_manager.SiteManagerClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.list_vantage_points = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await list_vantage_points(mock_settings)

        assert result == []
        mock_client.list_vantage_points.assert_called_once()


@pytest.mark.asyncio
async def test_list_vantage_points_with_inactive(mock_settings):
    """Test Vantage Points including inactive ones."""
    mock_response = {
        "vantage_points": [
            {
                "vantage_point_id": "vp-1",
                "name": "Active Office",
                "location": "NYC",
                "status": "active",
                "site_ids": ["site-1"],
            },
            {
                "vantage_point_id": "vp-2",
                "name": "Inactive Office",
                "location": "LA",
                "status": "inactive",
                "site_ids": [],
            },
        ]
    }

    with patch("src.tools.site_manager.SiteManagerClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.list_vantage_points = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await list_vantage_points(mock_settings)

        assert len(result) == 2
        assert result[0]["status"] == "active"
        assert result[1]["status"] == "inactive"


@pytest.mark.asyncio
async def test_list_vantage_points_disabled(mock_settings_disabled):
    """Test that function raises when site manager is disabled."""
    with pytest.raises(ValueError) as excinfo:
        await list_vantage_points(mock_settings_disabled)

    assert "Site Manager API is not enabled" in str(excinfo.value)


@pytest.mark.asyncio
async def test_list_vantage_points_list_format(mock_settings):
    """Test handling when response is a list instead of dict."""
    mock_response = [
        {
            "vantage_point_id": "vp-1",
            "name": "Office",
            "status": "active",
            "site_ids": [],
        }
    ]

    with patch("src.tools.site_manager.SiteManagerClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.list_vantage_points = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await list_vantage_points(mock_settings)

        assert len(result) == 1
        assert result[0]["vantage_point_id"] == "vp-1"
