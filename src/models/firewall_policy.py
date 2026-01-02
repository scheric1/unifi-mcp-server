from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PolicyAction(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"


class MatchingTarget(str, Enum):
    ANY = "ANY"
    IP = "IP"
    NETWORK = "NETWORK"
    REGION = "REGION"
    CLIENT = "CLIENT"


class ConnectionStateType(str, Enum):
    ALL = "ALL"
    CUSTOM = "CUSTOM"
    RESPOND_ONLY = "RESPOND_ONLY"


class IPVersion(str, Enum):
    BOTH = "BOTH"
    IPV4 = "IPV4"
    IPV6 = "IPV6"


class MatchTarget(BaseModel):
    zone_id: str = Field(..., description="Firewall zone ID")
    matching_target: MatchingTarget = Field(..., description="Target matching type")
    matching_target_type: Optional[str] = Field(None, description="Target type qualifier")
    port_matching_type: Optional[str] = Field(None, description="Port matching type (ANY/SPECIFIC)")
    port: Optional[str] = Field(None, description="Port(s) e.g. '53', '80,443', '1000-2000'")
    match_opposite_ports: Optional[bool] = Field(None, description="Invert port matching")
    ips: Optional[list[str]] = Field(None, description="IP addresses for IP matching")
    match_opposite_ips: Optional[bool] = Field(None, description="Invert IP matching")
    network_ids: Optional[list[str]] = Field(None, description="Network IDs for NETWORK matching")
    match_opposite_networks: Optional[bool] = Field(None, description="Invert network matching")
    regions: Optional[list[str]] = Field(None, description="ISO country codes for REGION matching")
    client_macs: Optional[list[str]] = Field(None, description="MAC addresses for CLIENT matching")
    match_mac: Optional[bool] = Field(None, description="Match by MAC address")

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Schedule(BaseModel):
    mode: str = Field(..., description="Schedule mode (ALWAYS/CUSTOM)")
    date_start: Optional[str] = Field(None, description="Start date YYYY-MM-DD")
    date_end: Optional[str] = Field(None, description="End date YYYY-MM-DD")
    time_all_day: Optional[bool] = Field(None, description="All day or specific time")
    time_range_start: Optional[str] = Field(None, description="Start time HH:MM")
    time_range_end: Optional[str] = Field(None, description="End time HH:MM")
    repeat_on_days: Optional[list[str]] = Field(None, description="Days to repeat")

    model_config = ConfigDict(extra="allow")


class FirewallPolicy(BaseModel):
    id: str = Field(..., alias="_id", description="Unique policy identifier")
    name: str = Field(..., description="Policy name")
    action: PolicyAction = Field(..., description="Policy action (ALLOW/BLOCK)")
    enabled: bool = Field(True, description="Whether policy is active")
    predefined: bool = Field(False, description="Whether this is a system rule")
    index: int = Field(10000, description="Priority order (lower = higher priority)")
    protocol: str = Field("all", description="Protocol (all/tcp/udp/tcp_udp/icmpv6)")
    ip_version: IPVersion = Field(IPVersion.BOTH, description="IP version filter")
    connection_state_type: ConnectionStateType = Field(
        ConnectionStateType.ALL, description="Connection state matching type"
    )
    connection_states: Optional[list[str]] = Field(
        None, description="Connection states when type is CUSTOM"
    )
    create_allow_respond: Optional[bool] = Field(None, description="Auto-allow response traffic")
    logging: Optional[bool] = Field(None, description="Enable rule logging")
    match_ip_sec: Optional[bool] = Field(None, description="Match IPsec traffic")
    match_opposite_protocol: Optional[bool] = Field(None, description="Match opposite protocol")
    icmp_typename: Optional[str] = Field(None, description="ICMP type name")
    icmp_v6_typename: Optional[str] = Field(None, description="ICMPv6 type name")
    description: Optional[str] = Field(None, description="Policy description")
    origin_id: Optional[str] = Field(None, description="Related origin object ID")
    origin_type: Optional[str] = Field(None, description="Origin type (e.g. port_forward)")
    source: MatchTarget = Field(..., description="Source matching criteria")
    destination: MatchTarget = Field(..., description="Destination matching criteria")
    schedule: Optional[Schedule] = Field(None, description="Time-based scheduling")

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class FirewallPolicyCreate(BaseModel):
    name: str = Field(..., description="Policy name")
    action: str = Field(..., description="Policy action (ALLOW/BLOCK)")
    enabled: bool = Field(True, description="Whether policy is active")
    protocol: str = Field("all", description="Protocol")
    ip_version: str = Field("BOTH", description="IP version filter")
    connection_state_type: str = Field("ALL", description="Connection state type")
    connection_states: Optional[list[str]] = Field(None, description="Connection states")
    source: dict = Field(..., description="Source matching criteria")
    destination: dict = Field(..., description="Destination matching criteria")
    description: Optional[str] = Field(None, description="Policy description")
    index: Optional[int] = Field(None, description="Priority order")
    schedule: Optional[dict] = Field(None, description="Time-based scheduling")

    model_config = ConfigDict(extra="allow")


class FirewallPolicyUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Policy name")
    action: Optional[str] = Field(None, description="Policy action")
    enabled: Optional[bool] = Field(None, description="Whether policy is active")
    protocol: Optional[str] = Field(None, description="Protocol")
    ip_version: Optional[str] = Field(None, description="IP version filter")
    connection_state_type: Optional[str] = Field(None, description="Connection state type")
    connection_states: Optional[list[str]] = Field(None, description="Connection states")
    source: Optional[dict] = Field(None, description="Source matching criteria")
    destination: Optional[dict] = Field(None, description="Destination matching criteria")
    description: Optional[str] = Field(None, description="Policy description")
    index: Optional[int] = Field(None, description="Priority order")
    schedule: Optional[dict] = Field(None, description="Time-based scheduling")

    model_config = ConfigDict(extra="allow")
