"""Unit tests for firewall_groups tools.

These exercise the legacy V1 internal endpoint
``/proxy/network/api/s/{site}/rest/firewallgroup`` (auto-translated by the
client from the ``/ea/sites/{site}/rest/firewallgroup`` shape used here).
The endpoint accepts an ``X-API-Key`` header on current UDM firmware, so
no session login is required, but it is local-gateway only — every tool
in the module is gated with ``_ensure_local_api``.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config import APIType, Settings
from src.tools import firewall_groups as fg
from src.utils.exceptions import ResourceNotFoundError


@pytest.fixture
def local_settings() -> MagicMock:
    settings = MagicMock(spec=Settings)
    settings.api_type = APIType.LOCAL
    settings.api_key = "test-api-key"
    settings.local_host = "192.0.2.1"
    settings.log_level = "INFO"
    return settings


@pytest.fixture
def cloud_settings() -> MagicMock:
    settings = MagicMock(spec=Settings)
    settings.api_type = APIType.CLOUD_EA
    settings.api_key = "test-api-key"
    settings.log_level = "INFO"
    return settings


@pytest.fixture
def sample_groups() -> list[dict[str, Any]]:
    """Three firewall groups across the three group types."""
    return [
        {
            "_id": "group-port-1",
            "name": "HomeKit-HAP",
            "group_type": "port-group",
            "group_members": ["8080", "9000-9010"],
            "site_id": "site-1",
            "external_id": "external-1",
        },
        {
            "_id": "group-addr-1",
            "name": "Trusted Subnets",
            "group_type": "address-group",
            "group_members": ["10.0.0.0/8", "192.168.50.0/24"],
            "site_id": "site-1",
            "external_id": "external-2",
        },
        {
            "_id": "group-port-2",
            "name": "RTSP-Streams",
            "group_type": "port-group",
            "group_members": ["554", "8554"],
            "site_id": "site-1",
            "external_id": "external-3",
        },
    ]


def _mock_client(get_response: Any = None) -> AsyncMock:
    client = AsyncMock()
    client.is_authenticated = True
    client.authenticate = AsyncMock()
    client.get = AsyncMock(return_value=get_response)
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


# --------------------------------------------------------------------------- #
# Local-API gate                                                              #
# --------------------------------------------------------------------------- #


class TestLocalApiGate:
    @pytest.mark.asyncio
    async def test_list_rejects_cloud(self, cloud_settings: MagicMock) -> None:
        with pytest.raises(NotImplementedError, match="UNIFI_API_TYPE='local'"):
            await fg.list_firewall_groups("default", cloud_settings)

    @pytest.mark.asyncio
    async def test_create_rejects_cloud(self, cloud_settings: MagicMock) -> None:
        with pytest.raises(NotImplementedError, match="UNIFI_API_TYPE='local'"):
            await fg.create_firewall_group(
                name="x",
                group_type="port-group",
                group_members=["80"],
                site_id="default",
                settings=cloud_settings,
                confirm=True,
            )


# --------------------------------------------------------------------------- #
# Read                                                                        #
# --------------------------------------------------------------------------- #


class TestListFirewallGroups:
    @pytest.mark.asyncio
    async def test_lists_all_groups(
        self, local_settings: MagicMock, sample_groups: list[dict[str, Any]]
    ) -> None:
        client = _mock_client(get_response={"meta": {"rc": "ok"}, "data": sample_groups})
        with patch("src.tools.firewall_groups.UniFiClient") as MockClient:
            MockClient.return_value = client
            result = await fg.list_firewall_groups("default", local_settings)

        assert len(result) == 3
        assert {g["name"] for g in result} == {
            "HomeKit-HAP",
            "Trusted Subnets",
            "RTSP-Streams",
        }
        endpoint = client.get.call_args.args[0]
        assert endpoint.endswith("/rest/firewallgroup")

    @pytest.mark.asyncio
    async def test_filter_by_group_type(
        self, local_settings: MagicMock, sample_groups: list[dict[str, Any]]
    ) -> None:
        client = _mock_client(get_response={"data": sample_groups})
        with patch("src.tools.firewall_groups.UniFiClient") as MockClient:
            MockClient.return_value = client
            result = await fg.list_firewall_groups(
                "default", local_settings, group_type="port-group"
            )
        assert len(result) == 2
        assert all(g["group_type"] == "port-group" for g in result)

    @pytest.mark.asyncio
    async def test_invalid_group_type_raises(
        self, local_settings: MagicMock
    ) -> None:
        with pytest.raises(ValueError, match="Invalid group_type"):
            await fg.list_firewall_groups(
                "default", local_settings, group_type="bogus-group"
            )

    @pytest.mark.asyncio
    async def test_handles_raw_list_response(
        self, local_settings: MagicMock, sample_groups: list[dict[str, Any]]
    ) -> None:
        client = _mock_client(get_response=sample_groups)
        with patch("src.tools.firewall_groups.UniFiClient") as MockClient:
            MockClient.return_value = client
            result = await fg.list_firewall_groups("default", local_settings)
        assert len(result) == 3


class TestGetFirewallGroup:
    @pytest.mark.asyncio
    async def test_returns_first_item(
        self, local_settings: MagicMock, sample_groups: list[dict[str, Any]]
    ) -> None:
        client = _mock_client(get_response={"data": [sample_groups[0]]})
        with patch("src.tools.firewall_groups.UniFiClient") as MockClient:
            MockClient.return_value = client
            result = await fg.get_firewall_group(
                "group-port-1", "default", local_settings
            )
        assert result["id"] == "group-port-1"
        assert result["name"] == "HomeKit-HAP"

    @pytest.mark.asyncio
    async def test_empty_data_raises(self, local_settings: MagicMock) -> None:
        client = _mock_client(get_response={"meta": {"rc": "ok"}, "data": []})
        with patch("src.tools.firewall_groups.UniFiClient") as MockClient:
            MockClient.return_value = client
            with pytest.raises(ResourceNotFoundError):
                await fg.get_firewall_group("missing", "default", local_settings)


# --------------------------------------------------------------------------- #
# Create                                                                      #
# --------------------------------------------------------------------------- #


class TestCreateFirewallGroup:
    @pytest.mark.asyncio
    async def test_create_port_group_round_trip(
        self, local_settings: MagicMock, sample_groups: list[dict[str, Any]]
    ) -> None:
        client = _mock_client()
        client.post.return_value = {"data": [sample_groups[0]]}

        with patch("src.tools.firewall_groups.UniFiClient") as MockClient:
            MockClient.return_value = client
            result = await fg.create_port_group(
                name="HomeKit-HAP",
                ports=["8080", "9000-9010"],
                site_id="default",
                settings=local_settings,
                confirm=True,
            )

        assert result["name"] == "HomeKit-HAP"
        assert result["group_type"] == "port-group"
        post_body = client.post.call_args.kwargs["json_data"]
        assert post_body["group_type"] == "port-group"
        assert post_body["group_members"] == ["8080", "9000-9010"]

    @pytest.mark.asyncio
    async def test_create_address_group_round_trip(
        self, local_settings: MagicMock, sample_groups: list[dict[str, Any]]
    ) -> None:
        client = _mock_client()
        client.post.return_value = {"data": [sample_groups[1]]}

        with patch("src.tools.firewall_groups.UniFiClient") as MockClient:
            MockClient.return_value = client
            result = await fg.create_address_group(
                name="Trusted Subnets",
                addresses=["10.0.0.0/8", "192.168.50.0/24"],
                site_id="default",
                settings=local_settings,
                confirm=True,
            )

        assert result["group_type"] == "address-group"
        post_body = client.post.call_args.kwargs["json_data"]
        assert post_body["group_type"] == "address-group"
        assert post_body["group_members"] == ["10.0.0.0/8", "192.168.50.0/24"]

    @pytest.mark.asyncio
    async def test_create_dry_run_does_not_post(
        self, local_settings: MagicMock
    ) -> None:
        client = _mock_client()
        with patch("src.tools.firewall_groups.UniFiClient") as MockClient:
            MockClient.return_value = client
            result = await fg.create_port_group(
                name="dry",
                ports=["80"],
                site_id="default",
                settings=local_settings,
                confirm=True,
                dry_run=True,
            )
        assert result["status"] == "dry_run"
        client.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_without_confirm_raises(
        self, local_settings: MagicMock
    ) -> None:
        with pytest.raises(ValueError, match="confirm=True"):
            await fg.create_port_group(
                name="x",
                ports=["80"],
                site_id="default",
                settings=local_settings,
                confirm=False,
            )

    @pytest.mark.asyncio
    async def test_create_string_false_confirm_does_not_bypass(
        self, local_settings: MagicMock
    ) -> None:
        """confirm='False' (truthy string) must NOT bypass the gate."""
        with pytest.raises(ValueError, match="confirm=True"):
            await fg.create_port_group(
                name="x",
                ports=["80"],
                site_id="default",
                settings=local_settings,
                confirm="False",
            )

    @pytest.mark.asyncio
    async def test_invalid_group_type_raises(
        self, local_settings: MagicMock
    ) -> None:
        with pytest.raises(ValueError, match="Invalid group_type"):
            await fg.create_firewall_group(
                name="x",
                group_type="bogus",
                group_members=["80"],
                site_id="default",
                settings=local_settings,
                confirm=True,
            )

    @pytest.mark.asyncio
    async def test_non_list_members_raises(
        self, local_settings: MagicMock
    ) -> None:
        with pytest.raises(ValueError, match="must be a list"):
            await fg.create_firewall_group(
                name="x",
                group_type="port-group",
                group_members="80",  # type: ignore[arg-type]
                site_id="default",
                settings=local_settings,
                confirm=True,
            )


# --------------------------------------------------------------------------- #
# Update                                                                      #
# --------------------------------------------------------------------------- #


class TestUpdateFirewallGroup:
    @pytest.mark.asyncio
    async def test_update_get_merge_put(
        self, local_settings: MagicMock, sample_groups: list[dict[str, Any]]
    ) -> None:
        existing = sample_groups[0]
        client = _mock_client(get_response={"data": [existing]})
        client.put.return_value = {
            "data": [{**existing, "group_members": ["8080", "9000-9010", "5555"]}]
        }

        with patch("src.tools.firewall_groups.UniFiClient") as MockClient:
            MockClient.return_value = client
            result = await fg.update_firewall_group(
                group_id="group-port-1",
                site_id="default",
                settings=local_settings,
                group_members=["8080", "9000-9010", "5555"],
                confirm=True,
            )

        assert result["group_members"] == ["8080", "9000-9010", "5555"]
        # PUT body must be the full merged object with server-controlled
        # fields stripped.
        put_body = client.put.call_args.kwargs["json_data"]
        assert put_body["name"] == "HomeKit-HAP"
        assert put_body["group_type"] == "port-group"
        assert put_body["group_members"] == ["8080", "9000-9010", "5555"]
        assert "_id" not in put_body
        assert "site_id" not in put_body
        assert "external_id" not in put_body

    @pytest.mark.asyncio
    async def test_update_dry_run(
        self, local_settings: MagicMock, sample_groups: list[dict[str, Any]]
    ) -> None:
        client = _mock_client(get_response={"data": [sample_groups[0]]})
        with patch("src.tools.firewall_groups.UniFiClient") as MockClient:
            MockClient.return_value = client
            result = await fg.update_firewall_group(
                group_id="group-port-1",
                site_id="default",
                settings=local_settings,
                name="HAP-renamed",
                confirm=True,
                dry_run=True,
            )
        assert result["status"] == "dry_run"
        assert result["changes"]["name"] == "HAP-renamed"
        client.put.assert_not_called()


# --------------------------------------------------------------------------- #
# Delete                                                                      #
# --------------------------------------------------------------------------- #


class TestDeleteFirewallGroup:
    @pytest.mark.asyncio
    async def test_delete_success(self, local_settings: MagicMock) -> None:
        client = _mock_client()
        with patch("src.tools.firewall_groups.UniFiClient") as MockClient:
            MockClient.return_value = client
            result = await fg.delete_firewall_group(
                group_id="group-port-1",
                site_id="default",
                settings=local_settings,
                confirm=True,
            )
        assert result["status"] == "success"
        assert result["action"] == "deleted"
        client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_dry_run(self, local_settings: MagicMock) -> None:
        client = _mock_client()
        with patch("src.tools.firewall_groups.UniFiClient") as MockClient:
            MockClient.return_value = client
            result = await fg.delete_firewall_group(
                group_id="group-port-1",
                site_id="default",
                settings=local_settings,
                confirm=True,
                dry_run=True,
            )
        assert result["status"] == "dry_run"
        assert result["action"] == "would_delete"
        client.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_without_confirm_raises(
        self, local_settings: MagicMock
    ) -> None:
        with pytest.raises(ValueError, match="confirm=True"):
            await fg.delete_firewall_group(
                group_id="group-port-1",
                site_id="default",
                settings=local_settings,
                confirm=False,
            )
