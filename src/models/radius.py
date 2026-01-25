"""RADIUS profile data models."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RADIUSProfile(BaseModel):
    """UniFi RADIUS authentication profile."""

    id: str = Field(..., description="RADIUS profile ID", alias="_id")
    name: str = Field(..., description="Profile name")

    # Authentication server configuration
    auth_server: str = Field(..., description="Authentication server IP/hostname")
    auth_port: int = Field(1812, description="Authentication port")
    auth_secret: str | None = Field(None, description="Authentication server shared secret")

    # Accounting server configuration (optional)
    acct_server: str | None = Field(None, description="Accounting server IP/hostname")
    acct_port: int = Field(1813, description="Accounting port")
    acct_secret: str | None = Field(None, description="Accounting server shared secret")
    use_same_secret: bool = Field(True, description="Use auth_secret for accounting")

    # VLAN configuration
    vlan_enabled: bool = Field(False, description="VLAN assignment enabled")
    vlan_wlan_mode: str | None = Field(None, description="VLAN mode for WLAN")

    # Advanced settings
    enabled: bool = Field(True, description="Whether profile is enabled")
    interim_update_interval: int | None = Field(
        None, description="Interim accounting update interval (seconds)"
    )
    use_usg_accounting_server: bool = Field(False, description="Use USG as accounting proxy")

    # Metadata
    site_id: str | None = Field(None, description="Site ID")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "507f191e810c19729de860ea",
                "name": "Corporate RADIUS",
                "auth_server": "radius.example.com",
                "auth_port": 1812,
                "auth_secret": "secret123",
                "acct_port": 1813,
                "enabled": True,
                "vlan_enabled": True,
            }
        },
    )


class RADIUSAccount(BaseModel):
    """RADIUS user account for guest access."""

    id: str = Field(..., description="Account ID", alias="_id")
    name: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

    # Time-based settings
    enabled: bool = Field(True, description="Account is enabled")
    start_time: int | None = Field(None, description="Account activation time (Unix timestamp)")
    end_time: int | None = Field(None, description="Account expiration time (Unix timestamp)")

    # VLAN assignment
    vlan_id: int | None = Field(None, description="Assigned VLAN ID")

    # Tunnel settings (for WPA2-Enterprise)
    tunnel_type: int | None = Field(None, description="RADIUS tunnel type")
    tunnel_medium_type: int | None = Field(None, description="RADIUS tunnel medium type")

    # Metadata
    site_id: str = Field(..., description="Site ID")
    note: str | None = Field(None, description="Admin notes")

    model_config = ConfigDict(populate_by_name=True)


class GuestPortalConfig(BaseModel):
    """Guest portal customization configuration."""

    site_id: str = Field(..., description="Site ID")

    # Portal settings
    enabled: bool = Field(True, description="Guest portal enabled")
    portal_title: str = Field("Guest WiFi", description="Portal page title")
    redirect_enabled: bool = Field(False, description="Redirect after authentication")
    redirect_url: str | None = Field(None, description="Redirect URL")

    # Authentication method
    auth_method: Literal["none", "password", "voucher", "radius", "external"] = Field(
        "voucher", description="Authentication method"
    )
    password: str | None = Field(None, description="Portal password (if auth_method=password)")

    # Terms of service
    terms_of_service_enabled: bool = Field(False, description="Require ToS acceptance")
    terms_of_service_text: str | None = Field(None, description="Terms of service text")

    # Session limits
    session_timeout: int = Field(480, description="Session timeout in minutes (0=unlimited)")
    download_limit_kbps: int | None = Field(None, description="Download speed limit in kbps")
    upload_limit_kbps: int | None = Field(None, description="Upload speed limit in kbps")

    # Customization
    background_image_url: str | None = Field(None, description="Background image URL")
    logo_url: str | None = Field(None, description="Logo image URL")
    custom_css: str | None = Field(None, description="Custom CSS")

    model_config = ConfigDict(populate_by_name=True)


class HotspotPackage(BaseModel):
    """Hotspot package with time and bandwidth limits."""

    id: str = Field(..., description="Package ID", alias="_id")
    name: str = Field(..., description="Package name")

    # Time limits
    duration_minutes: int = Field(..., description="Duration in minutes")

    # Bandwidth limits
    download_limit_kbps: int | None = Field(None, description="Download speed limit in kbps")
    upload_limit_kbps: int | None = Field(None, description="Upload speed limit in kbps")

    # Data quotas
    download_quota_mb: int | None = Field(None, description="Download quota in MB")
    upload_quota_mb: int | None = Field(None, description="Upload quota in MB")

    # Pricing (for payment gateway integration)
    price: float | None = Field(None, description="Package price")
    currency: str = Field("USD", description="Currency code")

    # Metadata
    enabled: bool = Field(True, description="Package is available")
    site_id: str = Field(..., description="Site ID")

    model_config = ConfigDict(populate_by_name=True)
