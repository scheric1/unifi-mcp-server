"""Unit tests for Redis cache module."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

mock_redis = MagicMock()
mock_redis.asyncio = MagicMock()
mock_redis.asyncio.Redis = MagicMock
mock_redis.exceptions = MagicMock()
mock_redis.exceptions.RedisError = Exception
sys.modules["redis"] = mock_redis
sys.modules["redis.asyncio"] = mock_redis.asyncio
sys.modules["redis.exceptions"] = mock_redis.exceptions

from src.cache import CacheClient, CacheConfig, invalidate_cache  # noqa: E402


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.log_level = "INFO"
    settings.redis_host = "localhost"
    settings.redis_port = 6379
    settings.redis_db = 0
    settings.redis_password = None
    return settings


class TestCacheConfig:
    def test_get_ttl_sites(self):
        assert CacheConfig.get_ttl("sites") == 300

    def test_get_ttl_devices(self):
        assert CacheConfig.get_ttl("devices") == 60

    def test_get_ttl_clients(self):
        assert CacheConfig.get_ttl("clients") == 30

    def test_get_ttl_networks(self):
        assert CacheConfig.get_ttl("networks") == 300

    def test_get_ttl_unknown_returns_default(self):
        assert CacheConfig.get_ttl("unknown_resource") == 60

    def test_get_ttl_case_insensitive(self):
        assert CacheConfig.get_ttl("SITES") == 300
        assert CacheConfig.get_ttl("Devices") == 60


class TestCacheClientInit:
    def test_init_with_redis_available(self, mock_settings):
        with patch("src.cache.REDIS_AVAILABLE", True):
            client = CacheClient(mock_settings)

            assert client.enabled is True
            assert client._connected is False
            assert client._redis is None

    def test_init_with_redis_unavailable(self, mock_settings):
        with patch("src.cache.REDIS_AVAILABLE", False):
            client = CacheClient(mock_settings)

            assert client.enabled is False

    def test_init_disabled_explicitly(self, mock_settings):
        with patch("src.cache.REDIS_AVAILABLE", True):
            client = CacheClient(mock_settings, enabled=False)

            assert client.enabled is False


class TestCacheClientConnect:
    @pytest.mark.asyncio
    async def test_connect_success(self, mock_settings):
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()

        with patch("src.cache.REDIS_AVAILABLE", True):
            with patch("src.cache.redis.Redis", return_value=mock_redis_instance):
                client = CacheClient(mock_settings)
                result = await client.connect()

                assert result is True
                assert client._connected is True
                mock_redis_instance.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self, mock_settings):
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock(side_effect=Exception("Connection refused"))

        with patch("src.cache.REDIS_AVAILABLE", True):
            with patch("src.cache.redis.Redis", return_value=mock_redis_instance):
                client = CacheClient(mock_settings)
                result = await client.connect()

                assert result is False
                assert client._connected is False
                assert client.enabled is False

    @pytest.mark.asyncio
    async def test_connect_when_disabled(self, mock_settings):
        with patch("src.cache.REDIS_AVAILABLE", False):
            client = CacheClient(mock_settings)
            result = await client.connect()

            assert result is False

    @pytest.mark.asyncio
    async def test_connect_already_connected(self, mock_settings):
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()

        with patch("src.cache.REDIS_AVAILABLE", True):
            with patch("src.cache.redis.Redis", return_value=mock_redis_instance):
                client = CacheClient(mock_settings)
                await client.connect()
                result = await client.connect()

                assert result is True
                assert mock_redis_instance.ping.call_count == 1


class TestCacheClientGetSet:
    @pytest.mark.asyncio
    async def test_get_success(self, mock_settings):
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis_instance.get = AsyncMock(return_value='{"key": "value"}')

        with patch("src.cache.REDIS_AVAILABLE", True):
            with patch("src.cache.redis.Redis", return_value=mock_redis_instance):
                client = CacheClient(mock_settings)
                await client.connect()
                result = await client.get("test:key")

                assert result == {"key": "value"}
                mock_redis_instance.get.assert_called_once_with("test:key")

    @pytest.mark.asyncio
    async def test_get_miss(self, mock_settings):
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis_instance.get = AsyncMock(return_value=None)

        with patch("src.cache.REDIS_AVAILABLE", True):
            with patch("src.cache.redis.Redis", return_value=mock_redis_instance):
                client = CacheClient(mock_settings)
                await client.connect()
                result = await client.get("nonexistent:key")

                assert result is None

    @pytest.mark.asyncio
    async def test_get_when_disabled(self, mock_settings):
        with patch("src.cache.REDIS_AVAILABLE", False):
            client = CacheClient(mock_settings)
            result = await client.get("test:key")

            assert result is None

    @pytest.mark.asyncio
    async def test_set_success(self, mock_settings):
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis_instance.set = AsyncMock()

        with patch("src.cache.REDIS_AVAILABLE", True):
            with patch("src.cache.redis.Redis", return_value=mock_redis_instance):
                client = CacheClient(mock_settings)
                await client.connect()
                result = await client.set("test:key", {"data": "value"})

                assert result is True
                mock_redis_instance.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, mock_settings):
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis_instance.setex = AsyncMock()

        with patch("src.cache.REDIS_AVAILABLE", True):
            with patch("src.cache.redis.Redis", return_value=mock_redis_instance):
                client = CacheClient(mock_settings)
                await client.connect()
                result = await client.set("test:key", {"data": "value"}, ttl=60)

                assert result is True
                mock_redis_instance.setex.assert_called_once_with(
                    "test:key", 60, '{"data": "value"}'
                )

    @pytest.mark.asyncio
    async def test_set_when_disabled(self, mock_settings):
        with patch("src.cache.REDIS_AVAILABLE", False):
            client = CacheClient(mock_settings)
            result = await client.set("test:key", {"data": "value"})

            assert result is False


class TestCacheClientDelete:
    @pytest.mark.asyncio
    async def test_delete_success(self, mock_settings):
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis_instance.delete = AsyncMock(return_value=1)

        with patch("src.cache.REDIS_AVAILABLE", True):
            with patch("src.cache.redis.Redis", return_value=mock_redis_instance):
                client = CacheClient(mock_settings)
                await client.connect()
                result = await client.delete("test:key")

                assert result is True
                mock_redis_instance.delete.assert_called_once_with("test:key")

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_settings):
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis_instance.delete = AsyncMock(return_value=0)

        with patch("src.cache.REDIS_AVAILABLE", True):
            with patch("src.cache.redis.Redis", return_value=mock_redis_instance):
                client = CacheClient(mock_settings)
                await client.connect()
                result = await client.delete("nonexistent:key")

                assert result is False

    @pytest.mark.asyncio
    async def test_delete_when_disabled(self, mock_settings):
        with patch("src.cache.REDIS_AVAILABLE", False):
            client = CacheClient(mock_settings)
            result = await client.delete("test:key")

            assert result is False


class TestCacheClientDeletePattern:
    @pytest.mark.asyncio
    async def test_delete_pattern_success(self, mock_settings):
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()

        async def mock_scan_iter(match=None):
            for key in ["sites:default:1", "sites:default:2", "sites:default:3"]:
                yield key

        mock_redis_instance.scan_iter = mock_scan_iter
        mock_redis_instance.delete = AsyncMock(return_value=3)

        with patch("src.cache.REDIS_AVAILABLE", True):
            with patch("src.cache.redis.Redis", return_value=mock_redis_instance):
                client = CacheClient(mock_settings)
                await client.connect()
                result = await client.delete_pattern("sites:*")

                assert result == 3

    @pytest.mark.asyncio
    async def test_delete_pattern_no_matches(self, mock_settings):
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()

        async def mock_scan_iter(match=None):
            return
            yield  # pragma: no cover

        mock_redis_instance.scan_iter = mock_scan_iter

        with patch("src.cache.REDIS_AVAILABLE", True):
            with patch("src.cache.redis.Redis", return_value=mock_redis_instance):
                client = CacheClient(mock_settings)
                await client.connect()
                result = await client.delete_pattern("nonexistent:*")

                assert result == 0


class TestCacheClientClear:
    @pytest.mark.asyncio
    async def test_clear_success(self, mock_settings):
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis_instance.flushdb = AsyncMock()

        with patch("src.cache.REDIS_AVAILABLE", True):
            with patch("src.cache.redis.Redis", return_value=mock_redis_instance):
                client = CacheClient(mock_settings)
                await client.connect()
                result = await client.clear()

                assert result is True
                mock_redis_instance.flushdb.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_when_disabled(self, mock_settings):
        with patch("src.cache.REDIS_AVAILABLE", False):
            client = CacheClient(mock_settings)
            result = await client.clear()

            assert result is False


class TestCacheClientExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, mock_settings):
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis_instance.exists = AsyncMock(return_value=1)

        with patch("src.cache.REDIS_AVAILABLE", True):
            with patch("src.cache.redis.Redis", return_value=mock_redis_instance):
                client = CacheClient(mock_settings)
                await client.connect()
                result = await client.exists("test:key")

                assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self, mock_settings):
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis_instance.exists = AsyncMock(return_value=0)

        with patch("src.cache.REDIS_AVAILABLE", True):
            with patch("src.cache.redis.Redis", return_value=mock_redis_instance):
                client = CacheClient(mock_settings)
                await client.connect()
                result = await client.exists("nonexistent:key")

                assert result is False


class TestCacheClientBuildKey:
    def test_build_key_simple(self, mock_settings):
        with patch("src.cache.REDIS_AVAILABLE", True):
            client = CacheClient(mock_settings)
            key = client.build_key("sites")

            assert key == "sites"

    def test_build_key_with_site_id(self, mock_settings):
        with patch("src.cache.REDIS_AVAILABLE", True):
            client = CacheClient(mock_settings)
            key = client.build_key("devices", site_id="default")

            assert key == "devices:default"

    def test_build_key_with_resource_id(self, mock_settings):
        with patch("src.cache.REDIS_AVAILABLE", True):
            client = CacheClient(mock_settings)
            key = client.build_key("devices", site_id="default", resource_id="device-123")

            assert key == "devices:default:device-123"

    def test_build_key_with_additional_params(self, mock_settings):
        with patch("src.cache.REDIS_AVAILABLE", True):
            client = CacheClient(mock_settings)
            key = client.build_key("clients", site_id="default", type="wireless")

            assert key == "clients:default:type:wireless"


class TestCacheClientDisconnect:
    @pytest.mark.asyncio
    async def test_disconnect_success(self, mock_settings):
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis_instance.close = AsyncMock()

        with patch("src.cache.REDIS_AVAILABLE", True):
            with patch("src.cache.redis.Redis", return_value=mock_redis_instance):
                client = CacheClient(mock_settings)
                await client.connect()
                await client.disconnect()

                assert client._redis is None
                assert client._connected is False
                mock_redis_instance.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self, mock_settings):
        with patch("src.cache.REDIS_AVAILABLE", True):
            client = CacheClient(mock_settings)
            await client.disconnect()


class TestInvalidateCache:
    @pytest.mark.asyncio
    async def test_invalidate_all(self, mock_settings):
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis_instance.flushdb = AsyncMock()
        mock_redis_instance.close = AsyncMock()

        with patch("src.cache.REDIS_AVAILABLE", True):
            with patch("src.cache.redis.Redis", return_value=mock_redis_instance):
                result = await invalidate_cache(mock_settings)

                assert result == -1
                mock_redis_instance.flushdb.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_by_resource_type(self, mock_settings):
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis_instance.close = AsyncMock()

        async def mock_scan_iter(match=None):
            for key in ["devices:default:1", "devices:default:2"]:
                yield key

        mock_redis_instance.scan_iter = mock_scan_iter
        mock_redis_instance.delete = AsyncMock(return_value=2)

        with patch("src.cache.REDIS_AVAILABLE", True):
            with patch("src.cache.redis.Redis", return_value=mock_redis_instance):
                result = await invalidate_cache(mock_settings, resource_type="devices")

                assert result == 2

    @pytest.mark.asyncio
    async def test_invalidate_by_site_id(self, mock_settings):
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis_instance.close = AsyncMock()

        async def mock_scan_iter(match=None):
            for key in ["devices:site1:1", "clients:site1:2"]:
                yield key

        mock_redis_instance.scan_iter = mock_scan_iter
        mock_redis_instance.delete = AsyncMock(return_value=2)

        with patch("src.cache.REDIS_AVAILABLE", True):
            with patch("src.cache.redis.Redis", return_value=mock_redis_instance):
                result = await invalidate_cache(mock_settings, site_id="site1")

                assert result == 2

    @pytest.mark.asyncio
    async def test_invalidate_when_redis_unavailable(self, mock_settings):
        with patch("src.cache.REDIS_AVAILABLE", False):
            result = await invalidate_cache(mock_settings)

            assert result == 0
