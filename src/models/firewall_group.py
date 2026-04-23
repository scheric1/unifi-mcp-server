"""Firewall group models.

Firewall groups on UniFi are the reusable objects that firewall policies
and legacy firewall rules reference for ports, IPv4 addresses, and IPv6
addresses. They live at the legacy V1 internal API endpoint
``/proxy/network/api/s/{site}/rest/firewallgroup`` — the v2 API does not
expose them, so these tools are local-gateway only.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


GroupType = Literal["port-group", "address-group", "ipv6-address-group"]


class FirewallGroup(BaseModel):
    """Firewall group object (port-group / address-group / ipv6-address-group).

    ``group_members`` holds a list of string values whose meaning depends on
    ``group_type``:

    * ``port-group`` — port numbers or ranges, e.g. ``["8080", "9000-9010"]``
    * ``address-group`` — IPv4 addresses or CIDR blocks
    * ``ipv6-address-group`` — IPv6 addresses or CIDR blocks
    """

    id: str = Field(..., alias="_id", description="Group identifier")
    name: str = Field(..., description="Group display name")
    group_type: str = Field(..., description="port-group / address-group / ipv6-address-group")
    group_members: list[str] = Field(
        default_factory=list,
        description="Ports (or addresses, depending on group_type)",
    )
    site_id: str | None = Field(
        None,
        description="Internal site id (not returned on every endpoint)",
    )
    external_id: str | None = Field(
        None,
        description="External UUID (not always present)",
    )

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class FirewallGroupCreate(BaseModel):
    """Request body for creating a new firewall group."""

    name: str = Field(..., description="Group display name")
    group_type: GroupType = Field(..., description="Group category")
    group_members: list[str] = Field(
        default_factory=list,
        description="List of ports or addresses",
    )

    model_config = ConfigDict(extra="allow")


class FirewallGroupUpdate(BaseModel):
    """Request body for updating an existing firewall group (partial update)."""

    name: str | None = Field(None, description="Group display name")
    group_members: list[str] | None = Field(
        None, description="New members list (replaces existing)"
    )

    model_config = ConfigDict(extra="allow")
