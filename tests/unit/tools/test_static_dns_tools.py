"""Tests for Static DNS tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tools.static_dns import (
    create_static_dns_entry,
    delete_static_dns_entry,
    list_static_dns_devices,
    list_static_dns_entries,
)
from src.utils.exceptions import ValidationError


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.log_level = "INFO"
    settings.api_type = MagicMock()
    settings.api_type.value = "local"
    settings.base_url = "https://192.168.1.1"
    settings.api_key = "test-key"
    settings.local_host = "192.168.1.1"
    settings.local_port = 443
    settings.local_verify_ssl = False
    return settings


class TestListStaticDNSEntries:
    @pytest.mark.asyncio
    async def test_list_entries_success(self, mock_settings):
        mock_entries = [
            {"_id": "dns1", "hostname": "server.local", "ipAddress": "192.168.1.1"},
            {"_id": "dns2", "hostname": "nas.local", "ipAddress": "192.168.1.2"},
        ]

        with patch("src.tools.static_dns.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.authenticate = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_entries)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await list_static_dns_entries("default", mock_settings)

            assert "entries" in result
            assert len(result["entries"]) == 2
            assert result["total"] == 2
            mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_entries_with_limit(self, mock_settings):
        mock_entries = [
            {"_id": "dns1", "hostname": "server1.local", "ipAddress": "192.168.1.1"},
            {"_id": "dns2", "hostname": "server2.local", "ipAddress": "192.168.1.2"},
            {"_id": "dns3", "hostname": "server3.local", "ipAddress": "192.168.1.3"},
        ]

        with patch("src.tools.static_dns.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.authenticate = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_entries)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await list_static_dns_entries("default", mock_settings, limit=2)

            assert len(result["entries"]) == 2

    @pytest.mark.asyncio
    async def test_list_entries_with_offset(self, mock_settings):
        mock_entries = [
            {"_id": "dns1", "hostname": "server1.local", "ipAddress": "192.168.1.1"},
            {"_id": "dns2", "hostname": "server2.local", "ipAddress": "192.168.1.2"},
            {"_id": "dns3", "hostname": "server3.local", "ipAddress": "192.168.1.3"},
        ]

        with patch("src.tools.static_dns.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.authenticate = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_entries)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await list_static_dns_entries("default", mock_settings, limit=2, offset=1)

            assert len(result["entries"]) == 2
            assert result["entries"][0]["_id"] == "dns2"

    @pytest.mark.asyncio
    async def test_list_entries_empty(self, mock_settings):
        with patch("src.tools.static_dns.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.authenticate = AsyncMock()
            mock_client.get = AsyncMock(return_value=[])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await list_static_dns_entries("default", mock_settings)

            assert result["entries"] == []
            assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_list_entries_dict_response(self, mock_settings):
        mock_response = {
            "data": [{"_id": "dns1", "hostname": "test.local", "ipAddress": "10.0.0.1"}]
        }

        with patch("src.tools.static_dns.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.authenticate = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await list_static_dns_entries("default", mock_settings)

            assert len(result["entries"]) == 1


class TestListStaticDNSDevices:
    @pytest.mark.asyncio
    async def test_list_devices_success(self, mock_settings):
        mock_devices = [
            {"mac": "aa:bb:cc:dd:ee:ff", "hostname": "workstation"},
            {"mac": "11:22:33:44:55:66", "hostname": "laptop"},
        ]

        with patch("src.tools.static_dns.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.authenticate = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_devices)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await list_static_dns_devices("default", mock_settings)

            assert "devices" in result
            assert len(result["devices"]) == 2
            assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_list_devices_with_limit(self, mock_settings):
        mock_devices = [
            {"mac": "aa:bb:cc:dd:ee:ff"},
            {"mac": "11:22:33:44:55:66"},
            {"mac": "77:88:99:aa:bb:cc"},
        ]

        with patch("src.tools.static_dns.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.authenticate = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_devices)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await list_static_dns_devices("default", mock_settings, limit=2)

            assert len(result["devices"]) == 2


class TestCreateStaticDNSEntry:
    @pytest.mark.asyncio
    async def test_create_requires_confirmation(self, mock_settings):
        with pytest.raises(ValidationError) as exc_info:
            await create_static_dns_entry(
                "default",
                mock_settings,
                hostname="test.local",
                ip_address="192.168.1.100",
                confirm=False,
            )
        assert "confirmation" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_dry_run(self, mock_settings):
        result = await create_static_dns_entry(
            "default",
            mock_settings,
            hostname="test.local",
            ip_address="192.168.1.100",
            confirm=True,
            dry_run=True,
        )

        assert result["dry_run"] is True
        assert "would_create" in result
        assert result["would_create"]["hostname"] == "test.local"
        assert result["would_create"]["ip_address"] == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_create_success(self, mock_settings):
        mock_response = {
            "_id": "dns123",
            "hostname": "newserver.local",
            "ipAddress": "192.168.1.200",
        }

        with patch("src.tools.static_dns.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.authenticate = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await create_static_dns_entry(
                "default",
                mock_settings,
                hostname="newserver.local",
                ip_address="192.168.1.200",
                confirm=True,
            )

            assert result["_id"] == "dns123"
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_with_description(self, mock_settings):
        mock_response = {"_id": "dns456", "hostname": "db.local", "description": "Database"}

        with patch("src.tools.static_dns.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.authenticate = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await create_static_dns_entry(
                "default",
                mock_settings,
                hostname="db.local",
                ip_address="10.0.0.50",
                description="Database server",
                confirm=True,
            )

            call_args = mock_client.post.call_args
            assert "description" in call_args.kwargs["json_data"]

    @pytest.mark.asyncio
    async def test_create_hostname_validation_empty(self, mock_settings):
        with pytest.raises(ValidationError) as exc_info:
            await create_static_dns_entry(
                "default",
                mock_settings,
                hostname="",
                ip_address="192.168.1.1",
                confirm=True,
            )
        assert "hostname" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_hostname_validation_too_long(self, mock_settings):
        long_hostname = "a" * 254
        with pytest.raises(ValidationError) as exc_info:
            await create_static_dns_entry(
                "default",
                mock_settings,
                hostname=long_hostname,
                ip_address="192.168.1.1",
                confirm=True,
            )
        assert "hostname" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_ip_validation_empty(self, mock_settings):
        with pytest.raises(ValidationError) as exc_info:
            await create_static_dns_entry(
                "default",
                mock_settings,
                hostname="test.local",
                ip_address="",
                confirm=True,
            )
        assert "ip" in str(exc_info.value).lower()


class TestDeleteStaticDNSEntry:
    @pytest.mark.asyncio
    async def test_delete_requires_confirmation(self, mock_settings):
        with pytest.raises(ValidationError) as exc_info:
            await delete_static_dns_entry(
                "default",
                mock_settings,
                entry_id="dns123",
                confirm=False,
            )
        assert "confirmation" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_delete_dry_run(self, mock_settings):
        result = await delete_static_dns_entry(
            "default",
            mock_settings,
            entry_id="dns123",
            confirm=True,
            dry_run=True,
        )

        assert result["dry_run"] is True
        assert result["would_delete"] == "dns123"

    @pytest.mark.asyncio
    async def test_delete_success(self, mock_settings):
        with patch("src.tools.static_dns.UniFiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.authenticate = AsyncMock()
            mock_client.delete = AsyncMock(return_value={"status": "ok"})
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await delete_static_dns_entry(
                "default",
                mock_settings,
                entry_id="dns456",
                confirm=True,
            )

            assert result["status"] == "deleted"
            assert result["entry_id"] == "dns456"
            mock_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_entry_id_validation(self, mock_settings):
        with pytest.raises(ValidationError) as exc_info:
            await delete_static_dns_entry(
                "default",
                mock_settings,
                entry_id="",
                confirm=True,
            )
        assert "entry id" in str(exc_info.value).lower()
