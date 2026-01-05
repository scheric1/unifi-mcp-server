"""Unit tests for Content Filtering models.

TDD: Write these tests FIRST, then implement src/models/content_filtering.py
Based on 117 categories from docs/research/schemas/content-filtering-categories.json
"""

import pytest
from pydantic import ValidationError


class TestContentCategory:
    """Tests for ContentCategory enum (117 categories)."""

    def test_family_value(self):
        """FAMILY should be a valid category."""
        from src.models.content_filtering import ContentCategory

        assert ContentCategory.FAMILY.value == "FAMILY"

    def test_advertisement_value(self):
        """ADVERTISEMENT should be a valid category."""
        from src.models.content_filtering import ContentCategory

        assert ContentCategory.ADVERTISEMENT.value == "ADVERTISEMENT"

    def test_adult_value(self):
        """ADULT should be a valid category."""
        from src.models.content_filtering import ContentCategory

        assert ContentCategory.ADULT.value == "ADULT"

    def test_malware_value(self):
        """MALWARE should be a valid category."""
        from src.models.content_filtering import ContentCategory

        assert ContentCategory.MALWARE.value == "MALWARE"

    def test_gambling_value(self):
        """GAMBLING should be a valid category."""
        from src.models.content_filtering import ContentCategory

        assert ContentCategory.GAMBLING.value == "GAMBLING"

    def test_social_networks_value(self):
        """SOCIAL_NETWORKS should be a valid category."""
        from src.models.content_filtering import ContentCategory

        assert ContentCategory.SOCIAL_NETWORKS.value == "SOCIAL_NETWORKS"

    def test_phishing_value(self):
        """PHISHING should be a valid category."""
        from src.models.content_filtering import ContentCategory

        assert ContentCategory.PHISHING.value == "PHISHING"

    def test_video_streaming_value(self):
        """VIDEO_STREAMING should be a valid category."""
        from src.models.content_filtering import ContentCategory

        assert ContentCategory.VIDEO_STREAMING.value == "VIDEO_STREAMING"

    def test_cryptomining_value(self):
        """CRYPTOMINING should be a valid category."""
        from src.models.content_filtering import ContentCategory

        assert ContentCategory.CRYPTOMINING.value == "CRYPTOMINING"

    def test_spyware_value(self):
        """SPYWARE should be a valid category."""
        from src.models.content_filtering import ContentCategory

        assert ContentCategory.SPYWARE.value == "SPYWARE"

    def test_invalid_category_raises(self):
        """Invalid category should raise ValueError."""
        from src.models.content_filtering import ContentCategory

        with pytest.raises(ValueError):
            ContentCategory("INVALID_CATEGORY")

    def test_total_categories_count(self):
        """Should have exactly 116 categories from UniFi schema."""
        from src.models.content_filtering import ContentCategory

        assert len(ContentCategory) == 116


class TestContentFilteringAction:
    """Tests for ContentFilteringAction enum."""

    def test_allow_value(self):
        """ALLOW should be a valid action."""
        from src.models.content_filtering import ContentFilteringAction

        assert ContentFilteringAction.ALLOW.value == "ALLOW"

    def test_block_value(self):
        """BLOCK should be a valid action."""
        from src.models.content_filtering import ContentFilteringAction

        assert ContentFilteringAction.BLOCK.value == "BLOCK"


class TestBlockedCategory:
    """Tests for BlockedCategory model."""

    def test_parse_basic_blocked_category(self):
        """Parse a basic blocked category."""
        from src.models.content_filtering import BlockedCategory, ContentCategory

        data = {"category": "ADULT", "enabled": True}
        blocked = BlockedCategory(**data)
        assert blocked.category == ContentCategory.ADULT
        assert blocked.enabled is True

    def test_parse_disabled_category(self):
        """Parse a disabled blocked category."""
        from src.models.content_filtering import BlockedCategory, ContentCategory

        data = {"category": "GAMBLING", "enabled": False}
        blocked = BlockedCategory(**data)
        assert blocked.category == ContentCategory.GAMBLING
        assert blocked.enabled is False

    def test_default_enabled_is_true(self):
        """Default enabled should be True."""
        from src.models.content_filtering import BlockedCategory

        data = {"category": "MALWARE"}
        blocked = BlockedCategory(**data)
        assert blocked.enabled is True

    def test_model_allows_extra_fields(self):
        """Model should allow extra fields from API."""
        from src.models.content_filtering import BlockedCategory

        data = {"category": "PHISHING", "enabled": True, "unknown_field": "value"}
        blocked = BlockedCategory(**data)
        assert blocked.category.value == "PHISHING"


class TestContentFilteringProfile:
    """Tests for ContentFilteringProfile model."""

    def test_parse_basic_profile(self):
        """Parse a basic content filtering profile."""
        from src.models.content_filtering import ContentFilteringProfile

        data = {
            "_id": "profile-123",
            "name": "Family Safe",
            "description": "Block adult content",
            "enabled": True,
        }
        profile = ContentFilteringProfile(**data)
        assert profile.id == "profile-123"
        assert profile.name == "Family Safe"
        assert profile.description == "Block adult content"
        assert profile.enabled is True

    def test_parse_profile_with_blocked_categories(self):
        """Parse profile with blocked categories list."""
        from src.models.content_filtering import ContentFilteringProfile

        data = {
            "_id": "profile-456",
            "name": "Work",
            "enabled": True,
            "blocked_categories": [
                {"category": "ADULT", "enabled": True},
                {"category": "GAMBLING", "enabled": True},
                {"category": "SOCIAL_NETWORKS", "enabled": False},
            ],
        }
        profile = ContentFilteringProfile(**data)
        assert profile.id == "profile-456"
        assert len(profile.blocked_categories) == 3
        assert profile.blocked_categories[0].category.value == "ADULT"
        assert profile.blocked_categories[2].enabled is False

    def test_default_blocked_categories_empty(self):
        """Default blocked_categories should be empty list."""
        from src.models.content_filtering import ContentFilteringProfile

        data = {"_id": "profile-789", "name": "Default"}
        profile = ContentFilteringProfile(**data)
        assert profile.blocked_categories == []

    def test_parse_profile_with_network_ids(self):
        """Parse profile with network IDs assigned."""
        from src.models.content_filtering import ContentFilteringProfile

        data = {
            "_id": "profile-abc",
            "name": "Guest Network",
            "enabled": True,
            "network_ids": ["network-1", "network-2"],
        }
        profile = ContentFilteringProfile(**data)
        assert len(profile.network_ids) == 2
        assert "network-1" in profile.network_ids

    def test_optional_fields_default(self):
        """Optional fields should have sensible defaults."""
        from src.models.content_filtering import ContentFilteringProfile

        data = {"_id": "min-profile", "name": "Minimal"}
        profile = ContentFilteringProfile(**data)
        assert profile.description is None
        assert profile.enabled is True
        assert profile.blocked_categories == []
        assert profile.network_ids == []

    def test_model_allows_extra_fields(self):
        """Model should allow extra fields from API."""
        from src.models.content_filtering import ContentFilteringProfile

        data = {
            "_id": "test",
            "name": "Test",
            "unknown_future_field": "value",
        }
        profile = ContentFilteringProfile(**data)
        assert profile.id == "test"


class TestContentFilteringConfig:
    """Tests for ContentFilteringConfig model (site-wide configuration)."""

    def test_parse_basic_config(self):
        """Parse a basic content filtering configuration."""
        from src.models.content_filtering import ContentFilteringConfig

        data = {
            "enabled": True,
            "block_page_enabled": True,
            "safe_search_enabled": False,
        }
        config = ContentFilteringConfig(**data)
        assert config.enabled is True
        assert config.block_page_enabled is True
        assert config.safe_search_enabled is False

    def test_parse_config_with_profiles(self):
        """Parse config with embedded profiles."""
        from src.models.content_filtering import ContentFilteringConfig

        data = {
            "enabled": True,
            "profiles": [
                {"_id": "p1", "name": "Default", "enabled": True},
                {"_id": "p2", "name": "Strict", "enabled": True},
            ],
        }
        config = ContentFilteringConfig(**data)
        assert len(config.profiles) == 2
        assert config.profiles[0].name == "Default"
        assert config.profiles[1].name == "Strict"

    def test_parse_config_with_blocked_categories(self):
        """Parse config with global blocked categories."""
        from src.models.content_filtering import ContentFilteringConfig

        data = {
            "enabled": True,
            "blocked_categories": ["ADULT", "MALWARE", "PHISHING"],
        }
        config = ContentFilteringConfig(**data)
        assert len(config.blocked_categories) == 3
        assert "ADULT" in config.blocked_categories

    def test_default_values(self):
        """Check default values for optional fields."""
        from src.models.content_filtering import ContentFilteringConfig

        data = {"enabled": True}
        config = ContentFilteringConfig(**data)
        assert config.block_page_enabled is False
        assert config.safe_search_enabled is False
        assert config.profiles == []
        assert config.blocked_categories == []

    def test_parse_config_with_custom_block_page(self):
        """Parse config with custom block page settings."""
        from src.models.content_filtering import ContentFilteringConfig

        data = {
            "enabled": True,
            "block_page_enabled": True,
            "block_page_url": "https://example.com/blocked",
            "block_page_message": "This content is blocked",
        }
        config = ContentFilteringConfig(**data)
        assert config.block_page_url == "https://example.com/blocked"
        assert config.block_page_message == "This content is blocked"

    def test_model_allows_extra_fields(self):
        """Model should allow extra fields from API."""
        from src.models.content_filtering import ContentFilteringConfig

        data = {
            "enabled": True,
            "some_new_api_field": "value",
        }
        config = ContentFilteringConfig(**data)
        assert config.enabled is True


class TestContentFilteringUpdate:
    """Tests for ContentFilteringUpdate model (for updating configuration)."""

    def test_create_update_with_enabled(self):
        """Create an update model with enabled flag."""
        from src.models.content_filtering import ContentFilteringUpdate

        update = ContentFilteringUpdate(enabled=True)
        assert update.enabled is True

    def test_create_update_with_blocked_categories(self):
        """Create an update model with blocked categories."""
        from src.models.content_filtering import ContentFilteringUpdate

        update = ContentFilteringUpdate(blocked_categories=["ADULT", "MALWARE"])
        assert update.blocked_categories == ["ADULT", "MALWARE"]

    def test_all_fields_optional(self):
        """All fields should be optional for partial updates."""
        from src.models.content_filtering import ContentFilteringUpdate

        update = ContentFilteringUpdate()
        assert update.enabled is None
        assert update.blocked_categories is None
        assert update.safe_search_enabled is None

    def test_create_update_with_safe_search(self):
        """Create an update model with safe search setting."""
        from src.models.content_filtering import ContentFilteringUpdate

        update = ContentFilteringUpdate(safe_search_enabled=True)
        assert update.safe_search_enabled is True


class TestContentCategoryInfo:
    """Tests for ContentCategoryInfo model (category metadata)."""

    def test_parse_category_info(self):
        """Parse category info with metadata."""
        from src.models.content_filtering import ContentCategoryInfo

        data = {
            "category": "ADULT",
            "name": "Adult Content",
            "description": "Websites containing adult content",
            "risk_level": "HIGH",
        }
        info = ContentCategoryInfo(**data)
        assert info.category == "ADULT"
        assert info.name == "Adult Content"
        assert info.description == "Websites containing adult content"
        assert info.risk_level == "HIGH"

    def test_parse_category_info_minimal(self):
        """Parse category info with minimal fields."""
        from src.models.content_filtering import ContentCategoryInfo

        data = {"category": "MALWARE", "name": "Malware"}
        info = ContentCategoryInfo(**data)
        assert info.category == "MALWARE"
        assert info.name == "Malware"
        assert info.description is None
        assert info.risk_level is None

    def test_model_allows_extra_fields(self):
        """Model should allow extra fields from API."""
        from src.models.content_filtering import ContentCategoryInfo

        data = {
            "category": "PHISHING",
            "name": "Phishing",
            "icon_url": "https://example.com/phishing.svg",
        }
        info = ContentCategoryInfo(**data)
        assert info.category == "PHISHING"
