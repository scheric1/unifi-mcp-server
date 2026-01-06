"""Tests for zbf_matrix tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_settings():
    from src.config import APIType

    settings = MagicMock(spec="Settings")
    settings.log_level = "INFO"
    settings.api_type = APIType.LOCAL
    settings.base_url = "https://192.168.1.1"
    settings.api_key = "test-key"
    settings.local_host = "192.168.1.1"
    settings.local_port = 443
    settings.local_verify_ssl = False
    settings.get_v2_api_path = MagicMock(
        side_effect=lambda site_id: f"/proxy/network/v2/api/site/{site_id}"
    )
    return settings


@pytest.fixture
def mock_settings_cloud():
    from src.config import APIType

    settings = MagicMock(spec="Settings")
    settings.log_level = "INFO"
    settings.api_type = APIType.CLOUD_EA
    return settings


@pytest.fixture
def sample_zbf_matrix():
    return [
        {
            "_id": "zone-internal",
            "name": "Internal",
            "zone_key": "internal",
            "data": [
                {"_id": "zone-external", "action": "block", "policy_count": 3},
                {"_id": "zone-gateway", "action": "allow", "policy_count": 1},
            ],
        },
        {
            "_id": "zone-external",
            "name": "External",
            "zone_key": "external",
            "data": [
                {"_id": "zone-internal", "action": "block", "policy_count": 5},
                {"_id": "zone-gateway", "action": "allow", "policy_count": 2},
            ],
        },
        {
            "_id": "zone-gateway",
            "name": "Gateway",
            "zone_key": "gateway",
            "data": [
                {"_id": "zone-internal", "action": "allow", "policy_count": 0},
                {"_id": "zone-external", "action": "allow", "policy_count": 0},
            ],
        },
    ]


class TestGetZbfMatrix:
    @pytest.mark.asyncio
    async def test_get_zbf_matrix_success(self, mock_settings, sample_zbf_matrix):
        from src.tools.zbf_matrix import get_zbf_matrix

        with patch("src.tools.zbf_matrix.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_zbf_matrix})

            result = await get_zbf_matrix("default", mock_settings)

            assert len(result) == 3
            assert result[0]["name"] == "Internal"
            mock_instance.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_zbf_matrix_list_response(self, mock_settings, sample_zbf_matrix):
        from src.tools.zbf_matrix import get_zbf_matrix

        with patch("src.tools.zbf_matrix.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_zbf_matrix)

            result = await get_zbf_matrix("default", mock_settings)

            assert len(result) == 3
            assert result[1]["name"] == "External"

    @pytest.mark.asyncio
    async def test_get_zbf_matrix_empty(self, mock_settings):
        from src.tools.zbf_matrix import get_zbf_matrix

        with patch("src.tools.zbf_matrix.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": []})

            result = await get_zbf_matrix("default", mock_settings)

            assert result == []

    @pytest.mark.asyncio
    async def test_get_zbf_matrix_requires_local_api(self, mock_settings_cloud):
        from src.tools.zbf_matrix import get_zbf_matrix
        from src.utils.exceptions import ValidationError

        with pytest.raises(ValidationError, match="local"):
            await get_zbf_matrix("default", mock_settings_cloud)


class TestGetZonePolicies:
    @pytest.mark.asyncio
    async def test_get_zone_policies_success(self, mock_settings, sample_zbf_matrix):
        from src.tools.zbf_matrix import get_zone_policies

        with patch("src.tools.zbf_matrix.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_zbf_matrix})

            result = await get_zone_policies("default", "zone-internal", mock_settings)

            assert result["name"] == "Internal"
            assert len(result["data"]) == 2

    @pytest.mark.asyncio
    async def test_get_zone_policies_not_found(self, mock_settings, sample_zbf_matrix):
        from src.tools.zbf_matrix import get_zone_policies

        with patch("src.tools.zbf_matrix.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_zbf_matrix})

            with pytest.raises(ValueError, match="not found"):
                await get_zone_policies("default", "zone-nonexistent", mock_settings)

    @pytest.mark.asyncio
    async def test_get_zone_policies_requires_local_api(self, mock_settings_cloud):
        from src.tools.zbf_matrix import get_zone_policies
        from src.utils.exceptions import ValidationError

        with pytest.raises(ValidationError, match="local"):
            await get_zone_policies("default", "zone-internal", mock_settings_cloud)


class TestGetZoneMatrixPolicy:
    @pytest.mark.asyncio
    async def test_get_zone_matrix_policy_success(self, mock_settings, sample_zbf_matrix):
        from src.tools.zbf_matrix import get_zone_matrix_policy

        with patch("src.tools.zbf_matrix.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_zbf_matrix})

            result = await get_zone_matrix_policy(
                "default", "zone-internal", "zone-external", mock_settings
            )

            assert result["source_zone_id"] == "zone-internal"
            assert result["destination_zone_id"] == "zone-external"
            assert result["action"] == "block"
            assert result["policy_count"] == 3

    @pytest.mark.asyncio
    async def test_get_zone_matrix_policy_not_found(self, mock_settings, sample_zbf_matrix):
        from src.tools.zbf_matrix import get_zone_matrix_policy

        with patch("src.tools.zbf_matrix.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_zbf_matrix})

            with pytest.raises(ValueError, match="No policy found"):
                await get_zone_matrix_policy(
                    "default", "zone-internal", "zone-nonexistent", mock_settings
                )

    @pytest.mark.asyncio
    async def test_get_zone_matrix_policy_source_not_found(self, mock_settings, sample_zbf_matrix):
        from src.tools.zbf_matrix import get_zone_matrix_policy

        with patch("src.tools.zbf_matrix.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_zbf_matrix})

            with pytest.raises(ValueError, match="not found"):
                await get_zone_matrix_policy(
                    "default", "zone-nonexistent", "zone-external", mock_settings
                )

    @pytest.mark.asyncio
    async def test_get_zone_matrix_policy_requires_local_api(self, mock_settings_cloud):
        from src.tools.zbf_matrix import get_zone_matrix_policy
        from src.utils.exceptions import ValidationError

        with pytest.raises(ValidationError, match="local"):
            await get_zone_matrix_policy(
                "default", "zone-internal", "zone-external", mock_settings_cloud
            )


class TestListZoneActions:
    @pytest.mark.asyncio
    async def test_list_zone_actions_success(self, mock_settings, sample_zbf_matrix):
        from src.tools.zbf_matrix import list_zone_actions

        with patch("src.tools.zbf_matrix.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_zbf_matrix})

            result = await list_zone_actions("default", mock_settings)

            assert "allow" in result["actions"]
            assert "block" in result["actions"]
            assert len(result["zones"]) == 3

    @pytest.mark.asyncio
    async def test_list_zone_actions_empty_matrix(self, mock_settings):
        from src.tools.zbf_matrix import list_zone_actions

        with patch("src.tools.zbf_matrix.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": []})

            result = await list_zone_actions("default", mock_settings)

            assert result["actions"] == []
            assert result["zones"] == []

    @pytest.mark.asyncio
    async def test_list_zone_actions_requires_local_api(self, mock_settings_cloud):
        from src.tools.zbf_matrix import list_zone_actions
        from src.utils.exceptions import ValidationError

        with pytest.raises(ValidationError, match="local"):
            await list_zone_actions("default", mock_settings_cloud)

    @pytest.mark.asyncio
    async def test_list_zone_actions_zone_details(self, mock_settings, sample_zbf_matrix):
        from src.tools.zbf_matrix import list_zone_actions

        with patch("src.tools.zbf_matrix.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": sample_zbf_matrix})

            result = await list_zone_actions("default", mock_settings)

            internal_zone = next(z for z in result["zones"] if z["name"] == "Internal")
            assert internal_zone["id"] == "zone-internal"
            assert internal_zone["key"] == "internal"
