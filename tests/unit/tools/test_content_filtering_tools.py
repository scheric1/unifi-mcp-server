"""Unit tests for content filtering tools.

TDD: Write these tests FIRST, then implement src/tools/content_filtering.py
Based on API endpoints:
- GET /proxy/network/v2/api/site/{site}/content-filtering/categories
- GET /proxy/network/v2/api/site/{site}/content-filtering
- PUT /proxy/network/v2/api/site/{site}/content-filtering
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config import Settings


@pytest.fixture
def mock_settings():
    settings = MagicMock(spec=Settings)
    settings.api_key = "test-api-key"
    settings.api_type = "local"
    settings.local_host = "192.168.1.1"
    settings.local_port = 443
    settings.local_verify_ssl = False
    settings.log_level = "INFO"
    return settings


@pytest.fixture
def sample_categories():
    return [
        {
            "category": "ADULT",
            "name": "Adult Content",
            "description": "Adult websites",
            "risk_level": "HIGH",
        },
        {
            "category": "MALWARE",
            "name": "Malware",
            "description": "Malicious software",
            "risk_level": "HIGH",
        },
        {
            "category": "GAMBLING",
            "name": "Gambling",
            "description": "Gambling sites",
            "risk_level": "MEDIUM",
        },
        {
            "category": "SOCIAL_NETWORKS",
            "name": "Social Networks",
            "description": "Social media",
            "risk_level": "LOW",
        },
        {
            "category": "PHISHING",
            "name": "Phishing",
            "description": "Phishing sites",
            "risk_level": "HIGH",
        },
    ]


@pytest.fixture
def sample_config():
    return {
        "enabled": True,
        "block_page_enabled": True,
        "safe_search_enabled": False,
        "profiles": [
            {
                "_id": "profile-1",
                "name": "Default",
                "enabled": True,
                "blocked_categories": [
                    {"category": "ADULT", "enabled": True},
                    {"category": "MALWARE", "enabled": True},
                ],
            }
        ],
        "blocked_categories": ["ADULT", "MALWARE", "PHISHING"],
    }


class TestListContentCategories:
    @pytest.mark.asyncio
    async def test_list_all_categories(self, mock_settings, sample_categories):
        from src.tools.content_filtering import list_content_categories

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_categories)

            result = await list_content_categories("default", mock_settings)

            assert len(result) == 5
            assert result[0]["category"] == "ADULT"

    @pytest.mark.asyncio
    async def test_categories_have_required_fields(self, mock_settings, sample_categories):
        from src.tools.content_filtering import list_content_categories

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_categories)

            result = await list_content_categories("default", mock_settings)

            for cat in result:
                assert "category" in cat
                assert "name" in cat

    @pytest.mark.asyncio
    async def test_empty_categories_response(self, mock_settings):
        from src.tools.content_filtering import list_content_categories

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=[])

            result = await list_content_categories("default", mock_settings)

            assert result == []

    @pytest.mark.asyncio
    async def test_api_error_handling(self, mock_settings):
        from src.tools.content_filtering import list_content_categories

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=Exception("API Error"))

            result = await list_content_categories("default", mock_settings)

            assert result == []

    @pytest.mark.asyncio
    async def test_correct_api_endpoint(self, mock_settings, sample_categories):
        from src.tools.content_filtering import list_content_categories

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_categories)

            await list_content_categories("test-site", mock_settings)

            call_args = mock_instance.get.call_args
            endpoint = call_args[0][0]
            assert "content-filtering/categories" in endpoint
            assert "test-site" in endpoint


class TestGetContentFilteringConfig:
    @pytest.mark.asyncio
    async def test_get_config(self, mock_settings, sample_config):
        from src.tools.content_filtering import get_content_filtering_config

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_config)

            result = await get_content_filtering_config("default", mock_settings)

            assert result["enabled"] is True
            assert result["block_page_enabled"] is True
            assert "profiles" in result

    @pytest.mark.asyncio
    async def test_config_includes_blocked_categories(self, mock_settings, sample_config):
        from src.tools.content_filtering import get_content_filtering_config

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_config)

            result = await get_content_filtering_config("default", mock_settings)

            assert "blocked_categories" in result
            assert "ADULT" in result["blocked_categories"]
            assert "MALWARE" in result["blocked_categories"]

    @pytest.mark.asyncio
    async def test_config_includes_profiles(self, mock_settings, sample_config):
        from src.tools.content_filtering import get_content_filtering_config

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_config)

            result = await get_content_filtering_config("default", mock_settings)

            assert len(result["profiles"]) == 1
            assert result["profiles"][0]["name"] == "Default"

    @pytest.mark.asyncio
    async def test_api_error_returns_default(self, mock_settings):
        from src.tools.content_filtering import get_content_filtering_config

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=Exception("API Error"))

            result = await get_content_filtering_config("default", mock_settings)

            assert result == {"enabled": False, "profiles": [], "blocked_categories": []}

    @pytest.mark.asyncio
    async def test_correct_api_endpoint(self, mock_settings, sample_config):
        from src.tools.content_filtering import get_content_filtering_config

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_config)

            await get_content_filtering_config("test-site", mock_settings)

            call_args = mock_instance.get.call_args
            endpoint = call_args[0][0]
            assert "content-filtering" in endpoint
            assert "test-site" in endpoint
            assert "categories" not in endpoint


class TestUpdateContentFiltering:
    @pytest.mark.asyncio
    async def test_update_requires_confirm(self, mock_settings):
        from src.tools.content_filtering import update_content_filtering

        result = await update_content_filtering(
            "default",
            mock_settings,
            enabled=True,
            confirm=False,
        )

        assert result["status"] == "error"
        assert "confirm=True" in result["message"]

    @pytest.mark.asyncio
    async def test_dry_run_returns_preview(self, mock_settings, sample_config):
        from src.tools.content_filtering import update_content_filtering

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_config)

            result = await update_content_filtering(
                "default",
                mock_settings,
                enabled=False,
                dry_run=True,
            )

            assert result["status"] == "preview"
            assert "changes" in result

    @pytest.mark.asyncio
    async def test_update_enabled_flag(self, mock_settings, sample_config):
        from src.tools.content_filtering import update_content_filtering

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_config)
            mock_instance.put = AsyncMock(return_value={"success": True})

            result = await update_content_filtering(
                "default",
                mock_settings,
                enabled=False,
                confirm=True,
            )

            assert result["status"] == "success"
            mock_instance.put.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_blocked_categories(self, mock_settings, sample_config):
        from src.tools.content_filtering import update_content_filtering

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_config)
            mock_instance.put = AsyncMock(return_value={"success": True})

            result = await update_content_filtering(
                "default",
                mock_settings,
                blocked_categories=["ADULT", "MALWARE", "GAMBLING"],
                confirm=True,
            )

            assert result["status"] == "success"
            call_args = mock_instance.put.call_args
            put_data = call_args[1].get("json", {})
            assert "blocked_categories" in put_data

    @pytest.mark.asyncio
    async def test_update_safe_search(self, mock_settings, sample_config):
        from src.tools.content_filtering import update_content_filtering

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_config)
            mock_instance.put = AsyncMock(return_value={"success": True})

            result = await update_content_filtering(
                "default",
                mock_settings,
                safe_search_enabled=True,
                confirm=True,
            )

            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_api_error_handling(self, mock_settings, sample_config):
        from src.tools.content_filtering import update_content_filtering

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_config)
            mock_instance.put = AsyncMock(side_effect=Exception("API Error"))

            result = await update_content_filtering(
                "default",
                mock_settings,
                enabled=True,
                confirm=True,
            )

            assert result["status"] == "error"
            assert "API Error" in result["message"]

    @pytest.mark.asyncio
    async def test_correct_api_endpoint(self, mock_settings, sample_config):
        from src.tools.content_filtering import update_content_filtering

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_config)
            mock_instance.put = AsyncMock(return_value={"success": True})

            await update_content_filtering(
                "test-site",
                mock_settings,
                enabled=True,
                confirm=True,
            )

            call_args = mock_instance.put.call_args
            endpoint = call_args[0][0]
            assert "content-filtering" in endpoint
            assert "test-site" in endpoint


class TestAuthenticationCalled:
    @pytest.mark.asyncio
    async def test_list_categories_authenticates(self, mock_settings, sample_categories):
        from src.tools.content_filtering import list_content_categories

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_categories)

            await list_content_categories("default", mock_settings)

            mock_instance.authenticate.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_config_authenticates(self, mock_settings, sample_config):
        from src.tools.content_filtering import get_content_filtering_config

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_config)

            await get_content_filtering_config("default", mock_settings)

            mock_instance.authenticate.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_authenticates(self, mock_settings, sample_config):
        from src.tools.content_filtering import update_content_filtering

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=sample_config)
            mock_instance.put = AsyncMock(return_value={"success": True})

            await update_content_filtering(
                "default",
                mock_settings,
                enabled=True,
                confirm=True,
            )

            mock_instance.authenticate.assert_called_once()


class TestNonDictResponses:
    @pytest.mark.asyncio
    async def test_categories_non_list_response(self, mock_settings):
        from src.tools.content_filtering import list_content_categories

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value={"data": []})

            result = await list_content_categories("default", mock_settings)

            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_config_non_dict_response(self, mock_settings):
        from src.tools.content_filtering import get_content_filtering_config

        with patch("src.tools.content_filtering.UniFiClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.is_authenticated = False
            mock_instance.authenticate = AsyncMock()
            mock_instance.get = AsyncMock(return_value=[])

            result = await get_content_filtering_config("default", mock_settings)

            assert "enabled" in result
