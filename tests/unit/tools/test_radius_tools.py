"""Tests for RADIUS and guest portal tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tools.radius import (
    configure_guest_portal,
    create_hotspot_package,
    create_radius_account,
    create_radius_profile,
    delete_hotspot_package,
    delete_radius_account,
    delete_radius_profile,
    get_guest_portal_config,
    get_radius_profile,
    list_hotspot_packages,
    list_radius_accounts,
    list_radius_profiles,
    update_radius_profile,
)
from src.utils.exceptions import ValidationError


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = MagicMock()
    settings.log_level = "INFO"
    settings.audit_log_enabled = False
    return settings


# =============================================================================
# RADIUS Profile Tests
# =============================================================================


@pytest.mark.asyncio
async def test_list_radius_profiles_success(mock_settings):
    """Test successful RADIUS profile listing."""
    mock_response = {
        "data": [
            {
                "_id": "profile-1",
                "name": "Corporate RADIUS",
                "auth_server": "radius.example.com",
                "auth_port": 1812,
                "acct_port": 1813,
                "enabled": True,
                "vlan_enabled": False,
            },
            {
                "_id": "profile-2",
                "name": "Guest RADIUS",
                "auth_server": "radius2.example.com",
                "auth_port": 1812,
                "enabled": True,
                "vlan_enabled": True,
            },
        ]
    }

    with patch("src.tools.radius.UniFiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.is_authenticated = False
        mock_client.authenticate = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await list_radius_profiles("default", mock_settings)

        assert len(result) == 2
        assert result[0]["id"] == "profile-1"
        assert result[0]["name"] == "Corporate RADIUS"
        assert result[1]["vlan_enabled"] is True
        mock_client.get.assert_called_once_with("/integration/v1/sites/default/radius/profiles")


@pytest.mark.asyncio
async def test_get_radius_profile_success(mock_settings):
    """Test getting specific RADIUS profile."""
    mock_response = {
        "data": {
            "_id": "profile-1",
            "name": "Corporate RADIUS",
            "auth_server": "radius.example.com",
            "auth_port": 1812,
            "auth_secret": "secret123",
            "acct_port": 1813,
            "enabled": True,
            "vlan_enabled": True,
        }
    }

    with patch("src.tools.radius.UniFiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.is_authenticated = False
        mock_client.authenticate = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await get_radius_profile("default", "profile-1", mock_settings)

        assert result["id"] == "profile-1"
        assert result["name"] == "Corporate RADIUS"
        assert result["vlan_enabled"] is True


@pytest.mark.asyncio
async def test_create_radius_profile_success(mock_settings):
    """Test creating a RADIUS profile."""
    mock_response = {
        "data": {
            "_id": "profile-new",
            "name": "New RADIUS",
            "auth_server": "radius.test.com",
            "auth_port": 1812,
            "enabled": True,
            "vlan_enabled": False,
        }
    }

    with patch("src.tools.radius.UniFiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.is_authenticated = False
        mock_client.authenticate = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await create_radius_profile(
            site_id="default",
            name="New RADIUS",
            auth_server="radius.test.com",
            auth_secret="test_secret",
            settings=mock_settings,
            confirm=True,
        )

        assert result["id"] == "profile-new"
        assert result["name"] == "New RADIUS"
        mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_create_radius_profile_dry_run(mock_settings):
    """Test create RADIUS profile dry run."""
    with patch("src.tools.radius.UniFiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.is_authenticated = False
        mock_client.authenticate = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await create_radius_profile(
            site_id="default",
            name="Test RADIUS",
            auth_server="radius.test.com",
            auth_secret="secret123",
            settings=mock_settings,
            confirm=True,
            dry_run=True,
        )

        assert result["dry_run"] is True
        assert result["payload"]["name"] == "Test RADIUS"
        assert result["payload"]["auth_secret"] == "***REDACTED***"


@pytest.mark.asyncio
async def test_create_radius_profile_no_confirm(mock_settings):
    """Test that creation fails without confirmation."""
    with pytest.raises(ValidationError) as excinfo:
        await create_radius_profile(
            site_id="default",
            name="Test",
            auth_server="radius.test.com",
            auth_secret="secret",
            settings=mock_settings,
            confirm=False,
        )

    assert "confirm=true" in str(excinfo.value)


@pytest.mark.asyncio
async def test_update_radius_profile_success(mock_settings):
    """Test updating a RADIUS profile."""
    mock_response = {
        "data": {
            "_id": "profile-1",
            "name": "Updated RADIUS",
            "auth_server": "radius.example.com",
            "auth_port": 1812,
            "enabled": True,
            "vlan_enabled": True,
        }
    }

    with patch("src.tools.radius.UniFiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.is_authenticated = False
        mock_client.authenticate = AsyncMock()
        mock_client.put = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await update_radius_profile(
            site_id="default",
            profile_id="profile-1",
            settings=mock_settings,
            name="Updated RADIUS",
            vlan_enabled=True,
            confirm=True,
        )

        assert result["name"] == "Updated RADIUS"
        assert result["vlan_enabled"] is True
        mock_client.put.assert_called_once()


@pytest.mark.asyncio
async def test_delete_radius_profile_success(mock_settings):
    """Test deleting a RADIUS profile."""
    with patch("src.tools.radius.UniFiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.is_authenticated = False
        mock_client.authenticate = AsyncMock()
        mock_client.delete = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await delete_radius_profile(
            site_id="default", profile_id="profile-1", settings=mock_settings, confirm=True
        )

        assert result["success"] is True
        assert "deleted successfully" in result["message"]
        mock_client.delete.assert_called_once_with(
            "/integration/v1/sites/default/radius/profiles/profile-1"
        )


# =============================================================================
# RADIUS Account Tests
# =============================================================================


@pytest.mark.asyncio
async def test_list_radius_accounts_success(mock_settings):
    """Test listing RADIUS accounts."""
    mock_response = {
        "data": [
            {
                "_id": "account-1",
                "name": "user1",
                "password": "password123",
                "enabled": True,
                "site_id": "default",
            },
            {
                "_id": "account-2",
                "name": "user2",
                "password": "password456",
                "enabled": False,
                "site_id": "default",
            },
        ]
    }

    with patch("src.tools.radius.UniFiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.is_authenticated = False
        mock_client.authenticate = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await list_radius_accounts("default", mock_settings)

        assert len(result) == 2
        assert result[0]["name"] == "user1"
        assert result[0]["password"] == "***REDACTED***"  # Password should be redacted


@pytest.mark.asyncio
async def test_create_radius_account_success(mock_settings):
    """Test creating a RADIUS account."""
    mock_response = {
        "data": {
            "_id": "account-new",
            "name": "newuser",
            "password": "newpass",
            "enabled": True,
            "vlan_id": 10,
            "site_id": "default",
        }
    }

    with patch("src.tools.radius.UniFiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.is_authenticated = False
        mock_client.authenticate = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await create_radius_account(
            site_id="default",
            username="newuser",
            password="newpass",
            settings=mock_settings,
            vlan_id=10,
            confirm=True,
        )

        assert result["id"] == "account-new"
        assert result["name"] == "newuser"
        assert result["password"] == "***REDACTED***"


@pytest.mark.asyncio
async def test_delete_radius_account_success(mock_settings):
    """Test deleting a RADIUS account."""
    with patch("src.tools.radius.UniFiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.is_authenticated = False
        mock_client.authenticate = AsyncMock()
        mock_client.delete = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await delete_radius_account(
            site_id="default", account_id="account-1", settings=mock_settings, confirm=True
        )

        assert result["success"] is True
        mock_client.delete.assert_called_once()


# =============================================================================
# Guest Portal Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_guest_portal_config_success(mock_settings):
    """Test getting guest portal configuration."""
    mock_response = {
        "data": {
            "site_id": "default",
            "enabled": True,
            "portal_title": "Guest WiFi",
            "auth_method": "voucher",
            "session_timeout": 480,
            "redirect_enabled": False,
        }
    }

    with patch("src.tools.radius.UniFiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.is_authenticated = False
        mock_client.authenticate = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await get_guest_portal_config("default", mock_settings)

        assert result["portal_title"] == "Guest WiFi"
        assert result["auth_method"] == "voucher"
        assert result["session_timeout"] == 480


@pytest.mark.asyncio
async def test_configure_guest_portal_success(mock_settings):
    """Test configuring guest portal."""
    mock_response = {
        "data": {
            "site_id": "default",
            "enabled": True,
            "portal_title": "Welcome!",
            "auth_method": "password",
            "session_timeout": 120,
            "redirect_enabled": True,
            "redirect_url": "https://example.com",
        }
    }

    with patch("src.tools.radius.UniFiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.is_authenticated = False
        mock_client.authenticate = AsyncMock()
        mock_client.put = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await configure_guest_portal(
            site_id="default",
            settings=mock_settings,
            portal_title="Welcome!",
            auth_method="password",
            session_timeout=120,
            redirect_enabled=True,
            redirect_url="https://example.com",
            confirm=True,
        )

        assert result["portal_title"] == "Welcome!"
        assert result["auth_method"] == "password"
        assert result["redirect_url"] == "https://example.com"
        mock_client.put.assert_called_once()


@pytest.mark.asyncio
async def test_configure_guest_portal_dry_run(mock_settings):
    """Test configure guest portal dry run."""
    with patch("src.tools.radius.UniFiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.is_authenticated = False
        mock_client.authenticate = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await configure_guest_portal(
            site_id="default",
            settings=mock_settings,
            portal_title="Test Portal",
            password="test123",
            confirm=True,
            dry_run=True,
        )

        assert result["dry_run"] is True
        assert result["payload"]["portal_title"] == "Test Portal"
        assert result["payload"]["password"] == "***REDACTED***"


# =============================================================================
# Hotspot Package Tests
# =============================================================================


@pytest.mark.asyncio
async def test_list_hotspot_packages_success(mock_settings):
    """Test listing hotspot packages."""
    mock_response = {
        "data": [
            {
                "_id": "package-1",
                "name": "1 Hour Basic",
                "duration_minutes": 60,
                "download_limit_kbps": 5000,
                "upload_limit_kbps": 1000,
                "enabled": True,
                "site_id": "default",
            },
            {
                "_id": "package-2",
                "name": "1 Day Premium",
                "duration_minutes": 1440,
                "download_limit_kbps": 50000,
                "upload_limit_kbps": 10000,
                "price": 9.99,
                "currency": "USD",
                "enabled": True,
                "site_id": "default",
            },
        ]
    }

    with patch("src.tools.radius.UniFiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.is_authenticated = False
        mock_client.authenticate = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await list_hotspot_packages("default", mock_settings)

        assert len(result) == 2
        assert result[0]["name"] == "1 Hour Basic"
        assert result[1]["price"] == 9.99


@pytest.mark.asyncio
async def test_create_hotspot_package_success(mock_settings):
    """Test creating a hotspot package."""
    mock_response = {
        "data": {
            "_id": "package-new",
            "name": "2 Hour Package",
            "duration_minutes": 120,
            "download_limit_kbps": 10000,
            "upload_limit_kbps": 2000,
            "price": 4.99,
            "currency": "USD",
            "enabled": True,
            "site_id": "default",
        }
    }

    with patch("src.tools.radius.UniFiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.is_authenticated = False
        mock_client.authenticate = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await create_hotspot_package(
            site_id="default",
            name="2 Hour Package",
            duration_minutes=120,
            settings=mock_settings,
            download_limit_kbps=10000,
            upload_limit_kbps=2000,
            price=4.99,
            confirm=True,
        )

        assert result["id"] == "package-new"
        assert result["name"] == "2 Hour Package"
        assert result["price"] == 4.99
        mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_create_hotspot_package_with_quotas(mock_settings):
    """Test creating hotspot package with data quotas."""
    mock_response = {
        "data": {
            "_id": "package-quota",
            "name": "Limited Data Package",
            "duration_minutes": 1440,
            "download_quota_mb": 1024,
            "upload_quota_mb": 256,
            "enabled": True,
            "site_id": "default",
        }
    }

    with patch("src.tools.radius.UniFiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.is_authenticated = False
        mock_client.authenticate = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await create_hotspot_package(
            site_id="default",
            name="Limited Data Package",
            duration_minutes=1440,
            settings=mock_settings,
            download_quota_mb=1024,
            upload_quota_mb=256,
            confirm=True,
        )

        assert result["download_quota_mb"] == 1024
        assert result["upload_quota_mb"] == 256


@pytest.mark.asyncio
async def test_delete_hotspot_package_success(mock_settings):
    """Test deleting a hotspot package."""
    with patch("src.tools.radius.UniFiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.is_authenticated = False
        mock_client.authenticate = AsyncMock()
        mock_client.delete = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await delete_hotspot_package(
            site_id="default", package_id="package-1", settings=mock_settings, confirm=True
        )

        assert result["success"] is True
        assert "deleted successfully" in result["message"]
        mock_client.delete.assert_called_once()
