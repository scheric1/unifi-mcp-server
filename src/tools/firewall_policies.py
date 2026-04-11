"""Firewall policies management tools for UniFi v2 API."""

from typing import Any

from ..api.client import UniFiClient
from ..config import APIType, Settings
from ..models.firewall_policy import (
    FirewallPolicy,
    FirewallPolicyCreate,
    FirewallZoneV2Mapping,
)
from ..utils import APIError, ResourceNotFoundError, get_logger, log_audit, sanitize_log_message
from ..utils.validators import coerce_bool

logger = get_logger(__name__)

# The v2 `firewall-policies` API uses internal MongoDB ObjectIds for zone_id,
# while the integration API (and most other MCP tools) return the public
# UUIDs as `external_id`. This cache maps both the external UUID, zone name,
# and zone_key to the internal ObjectId, populated on demand.
_zone_cache: dict[str, dict[str, str]] = {}

_VALID_IP_VERSIONS = ("IPV4", "IPV6", "BOTH")


def _extract_zone_list(response: Any) -> list[dict[str, Any]]:
    """Normalize a zone-listing response into a plain list of dicts.

    Handles the three shapes ``UniFiClient`` can return:
    - raw list (when the API response is ``{"data": [...]}``)
    - dict with ``data`` field (may be ``None`` or another list)
    - bare dict payload (unusual but defensively handled)
    """
    if isinstance(response, list):
        return [z for z in response if isinstance(z, dict)]
    if isinstance(response, dict):
        inner = response.get("data")
        if inner is None:
            return []
        if isinstance(inner, list):
            return [z for z in inner if isinstance(z, dict)]
    return []


def _ensure_local_api(settings: Settings) -> None:
    """Ensure the UniFi controller is accessed via the local API for v2 endpoints."""
    if settings.api_type != APIType.LOCAL:
        raise NotImplementedError(
            "Firewall policies (v2 API) are only available when UNIFI_API_TYPE='local'. "
            "Please configure a local UniFi gateway connection to use these tools."
        )


async def _load_zone_index(
    client: UniFiClient, settings: Settings, site_id: str
) -> dict[str, str]:
    """Fetch the v2 zone list and build a name/UUID → internal-_id index."""
    endpoint = f"{settings.get_v2_api_path(site_id)}/firewall/zone"
    response = await client.get(endpoint)
    zones = _extract_zone_list(response)

    index: dict[str, str] = {}
    for zone in zones:
        internal_id = zone.get("_id")
        if not internal_id:
            continue
        # Index the internal _id as itself so callers that already know the
        # ObjectId continue to work.
        index[internal_id] = internal_id
        if external_id := zone.get("external_id"):
            index[external_id] = internal_id
        if name := zone.get("name"):
            index[name.lower()] = internal_id
        if zone_key := zone.get("zone_key"):
            index[zone_key.lower()] = internal_id
    _zone_cache[site_id] = index
    return index


async def _resolve_zone_id(
    client: UniFiClient, settings: Settings, site_id: str, identifier: str
) -> str:
    """Resolve a zone name, external UUID, or internal ObjectId to the v2 API's
    internal zone _id. Raises ValueError if no match."""
    if not identifier:
        raise ValueError("Zone identifier is required")
    index = _zone_cache.get(site_id) or await _load_zone_index(client, settings, site_id)
    if identifier in index:
        return index[identifier]
    lowered = identifier.lower()
    if lowered in index:
        return index[lowered]
    # Refresh once in case the zone was created after the cache was populated.
    index = await _load_zone_index(client, settings, site_id)
    if identifier in index:
        return index[identifier]
    if lowered in index:
        return index[lowered]
    known_internal_ids = sorted({v for v in index.values()})
    raise ValueError(
        f"Could not resolve firewall zone '{identifier}'. Pass a zone name "
        f"(e.g. 'Internal'), external UUID, or internal _id. "
        f"Known internal zone ids: {known_internal_ids}"
    )


async def list_firewall_zones_v2(
    site_id: str,
    settings: Settings,
) -> list[dict[str, Any]]:
    """List firewall zones from the v2 API with internal + external IDs.

    The v2 ``firewall-policies`` endpoint uses internal MongoDB ObjectIds for
    zone_id, not the public integration API UUIDs. This tool returns the
    mapping so callers can hand either identifier (or the zone name) to
    ``create_firewall_policy`` / ``update_firewall_policy``.

    Args:
        site_id: Site identifier
        settings: Application settings

    Returns:
        List of :class:`FirewallZoneV2Mapping` dicts.

    Raises:
        NotImplementedError: When using cloud API
        APIError: When the API request fails
    """
    _ensure_local_api(settings)

    async with UniFiClient(settings) as client:
        logger.info(
            sanitize_log_message(f"Listing v2 firewall zones for site {site_id}")
        )

        if not client.is_authenticated:
            await client.authenticate()

        endpoint = f"{settings.get_v2_api_path(site_id)}/firewall/zone"
        try:
            response = await client.get(endpoint)
        except APIError:
            logger.exception(
                sanitize_log_message(
                    f"Failed to list v2 firewall zones for site {site_id}"
                )
            )
            raise

        zones = _extract_zone_list(response)

        return [
            FirewallZoneV2Mapping(
                internal_id=z.get("_id"),
                external_id=z.get("external_id"),
                name=z.get("name"),
                zone_key=z.get("zone_key"),
                default_zone=z.get("default_zone") or False,
                network_ids=z.get("network_ids") or [],
            ).model_dump()
            for z in zones
        ]


async def list_firewall_policies(
    site_id: str,
    settings: Settings,
) -> list[dict[str, Any]]:
    """List all firewall policies (Traffic & Firewall Rules) for a site.

    This tool fetches firewall policies from the UniFi v2 API endpoint.
    Only available with local gateway API (api_type="local").

    Args:
        site_id: Site identifier (default: "default")
        settings: Application settings

    Returns:
        List of firewall policy objects

    Raises:
        NotImplementedError: When using cloud API (v2 endpoints require local access)
        APIError: When API request fails

    Note:
        Cloud API does not support v2 endpoints. Configure UNIFI_API_TYPE=local
        and UNIFI_LOCAL_HOST to use this tool.
    """
    _ensure_local_api(settings)

    async with UniFiClient(settings) as client:
        logger.info(sanitize_log_message(f"Listing firewall policies for site {site_id}"))

        if not client.is_authenticated:
            await client.authenticate()

        endpoint = f"{settings.get_v2_api_path(site_id)}/firewall-policies"
        response = await client.get(endpoint)

        policies_data = response if isinstance(response, list) else response.get("data", [])

        return [FirewallPolicy(**policy).model_dump() for policy in policies_data]


async def get_firewall_policy(
    policy_id: str,
    site_id: str,
    settings: Settings,
) -> dict[str, Any]:
    """Get a specific firewall policy by ID.

    Retrieves detailed information about a single firewall policy
    from the v2 API endpoint.

    Args:
        policy_id: The firewall policy ID
        site_id: Site identifier (default: "default")
        settings: Application settings

    Returns:
        Firewall policy object

    Raises:
        NotImplementedError: When using cloud API (v2 endpoints require local access)
        ResourceNotFoundError: If policy not found
        APIError: When API request fails

    Note:
        Cloud API does not support v2 endpoints. Configure UNIFI_API_TYPE=local
        and UNIFI_LOCAL_HOST to use this tool.

    Example:
        >>> policy = await get_firewall_policy(
        ...     "682a0e42220317278bb0b2cb",
        ...     "default",
        ...     settings
        ... )
        >>> print(f"{policy['name']}: {policy['action']}")
    """
    _ensure_local_api(settings)

    async with UniFiClient(settings) as client:
        logger.info(sanitize_log_message(f"Getting firewall policy {policy_id} for site {site_id}"))

        if not client.is_authenticated:
            await client.authenticate()

        endpoint = f"{settings.get_v2_api_path(site_id)}/firewall-policies/{policy_id}"

        try:
            response = await client.get(endpoint)
        except ResourceNotFoundError as err:
            raise ResourceNotFoundError("firewall_policy", policy_id) from err

        # Handle both wrapped and unwrapped responses
        if isinstance(response, dict) and "data" in response:
            data = response["data"]
        else:
            data = response

        if not data:
            raise ResourceNotFoundError("firewall_policy", policy_id)

        return FirewallPolicy(**data).model_dump()


async def create_firewall_policy(
    name: str,
    action: str,
    site_id: str,
    settings: Settings,
    source_zone_id: str | None = None,
    destination_zone_id: str | None = None,
    source_matching_target: str = "ANY",
    destination_matching_target: str = "ANY",
    protocol: str = "all",
    enabled: bool = True,
    description: str | None = None,
    ip_version: str = "BOTH",
    confirm: bool | str = False,
    dry_run: bool | str = False,
) -> dict[str, Any]:
    """Create a new firewall policy (Traffic & Firewall Rule).

    Only available with local gateway API (api_type="local").
    Requires confirm=True to execute. Use dry_run=True to preview.

    Args:
        name: Policy name
        action: ALLOW or BLOCK
        site_id: Site identifier
        settings: Application settings
        source_zone_id: Source zone — accepts a zone name (e.g. "Internal"),
            public integration-API UUID, or internal ObjectId. All forms are
            resolved to the v2 API's internal zone _id automatically.
        destination_zone_id: Destination zone (same identifier flexibility as
            source)
        source_matching_target: ANY, IP, NETWORK, REGION, or CLIENT
        destination_matching_target: ANY, IP, NETWORK, or REGION
        protocol: all, tcp, udp, tcp_udp, or icmpv6
        enabled: Whether policy is active
        description: Optional description
        ip_version: IPV4, IPV6, or BOTH (required by API; defaults to BOTH)
        confirm: REQUIRED True for mutating operations
        dry_run: Preview changes without applying

    Returns:
        Created firewall policy object or dry-run preview

    Raises:
        ValueError: If confirm not True, invalid action, or zone cannot be
            resolved.
        NotImplementedError: When using cloud API
    """
    _ensure_local_api(settings)

    valid_actions = ["ALLOW", "BLOCK"]
    action_upper = action.upper()
    if action_upper not in valid_actions:
        raise ValueError(f"Invalid action '{action}'. Must be one of: {valid_actions}")

    ip_version_upper = ip_version.upper()
    if ip_version_upper not in _VALID_IP_VERSIONS:
        raise ValueError(
            f"Invalid ip_version '{ip_version}'. Must be one of: {list(_VALID_IP_VERSIONS)}"
        )

    # Coerce string inputs ("true"/"false") to real booleans — MCP clients
    # may serialise these flags as strings and plain truthiness would treat
    # "False" as True, bypassing the confirmation gate entirely.
    confirm_bool = coerce_bool(confirm)
    dry_run_bool = coerce_bool(dry_run)

    if not dry_run_bool and not confirm_bool:
        raise ValueError(
            "This operation requires confirm=True to execute. "
            "Use dry_run=True to preview changes first."
        )

    parameters = {
        "site_id": site_id,
        "name": name,
        "action": action_upper,
        "enabled": enabled,
        "source_zone_id": source_zone_id,
        "destination_zone_id": destination_zone_id,
    }

    try:
        async with UniFiClient(settings) as client:
            logger.info(sanitize_log_message(f"Creating firewall policy '{name}' for site {site_id}"))

            if not client.is_authenticated:
                await client.authenticate()

            # Resolve zone identifiers to internal _ids expected by the v2 API.
            source_config: dict[str, Any] = {
                "matching_target": source_matching_target.upper()
            }
            if source_zone_id:
                source_config["zone_id"] = await _resolve_zone_id(
                    client, settings, site_id, source_zone_id
                )

            destination_config: dict[str, Any] = {
                "matching_target": destination_matching_target.upper()
            }
            if destination_zone_id:
                destination_config["zone_id"] = await _resolve_zone_id(
                    client, settings, site_id, destination_zone_id
                )

            # The v2 firewall-policies endpoint requires `schedule` and
            # `ip_version`; the API 400s (with an obfuscated Spring error)
            # if either is omitted. Default to an always-on rule.
            policy_data = FirewallPolicyCreate(
                name=name,
                action=action_upper,
                enabled=enabled,
                protocol=protocol,
                ip_version=ip_version_upper,
                source=source_config,
                destination=destination_config,
                description=description,
                schedule={"mode": "ALWAYS"},
            )

            if dry_run_bool:
                logger.info(
                    sanitize_log_message(
                        f"DRY RUN: Would create firewall policy '{name}' in site '{site_id}'"
                    )
                )
                log_audit(
                    operation="create_firewall_policy",
                    parameters=parameters,
                    result="dry_run",
                    site_id=site_id,
                    dry_run=True,
                )
                return {
                    "status": "dry_run",
                    "message": f"Would create firewall policy '{name}'",
                    "policy": policy_data.model_dump(exclude_none=True),
                }

            endpoint = f"{settings.get_v2_api_path(site_id)}/firewall-policies"
            response = await client.post(
                endpoint, json_data=policy_data.model_dump(exclude_none=True)
            )

            if isinstance(response, dict) and "data" in response:
                data = response["data"]
            else:
                data = response

            logger.info(sanitize_log_message(f"Created firewall policy '{name}' in site '{site_id}'"))
            log_audit(
                operation="create_firewall_policy",
                parameters=parameters,
                result="success",
                site_id=site_id,
            )

            return FirewallPolicy(**data).model_dump()

    except Exception as e:
        logger.error(sanitize_log_message(f"Failed to create firewall policy '{name}': {e}"))
        log_audit(
            operation="create_firewall_policy",
            parameters=parameters,
            result="failed",
            site_id=site_id,
        )
        raise


async def update_firewall_policy(
    policy_id: str,
    site_id: str = "default",
    settings: Settings = None,
    name: str | None = None,
    action: str | None = None,
    enabled: bool | None = None,
    logging: bool | None = None,
    ip_version: str | None = None,
    protocol: str | None = None,
    description: str | None = None,
    confirm: bool | str = False,
    dry_run: bool | str = False,
) -> dict[str, Any]:
    """Update an existing firewall policy.

    The v2 ``firewall-policies`` PUT endpoint requires the **full** policy
    object — a partial payload like ``{"logging": true}`` is rejected with
    ``Validation failed ... field 'action': rejected value [null]``. To
    support partial updates from the caller's perspective, this tool
    fetches the existing policy, merges in the provided field overrides,
    strips ``_id`` / ``predefined`` (which the API controls), and PUTs the
    merged object back.

    Args:
        policy_id: ID of policy to update
        site_id: Site identifier
        settings: Application settings
        name: New policy name
        action: New action ALLOW/BLOCK
        enabled: Enable/disable the policy
        logging: Toggle firewall rule logging. Forces CPU inspection of the
            matched flows, which makes them visible in the v2 traffic-flows
            endpoint (default-allowed inter-VLAN traffic is normally
            hardware-offloaded and never reaches the flow table).
        ip_version: IPV4 / IPV6 / BOTH
        protocol: Transport protocol (all, tcp, udp, tcp_udp, icmpv6)
        description: Free-form description
        confirm: REQUIRED True for mutating operations
        dry_run: Preview changes without applying

    Returns:
        Updated policy object

    Raises:
        NotImplementedError: When using cloud API (v2 endpoints require local access)
        ValueError: If confirmation not provided or an invalid value is supplied
        ResourceNotFoundError: If policy not found
    """
    _ensure_local_api(settings)

    confirm_bool = coerce_bool(confirm)
    dry_run_bool = coerce_bool(dry_run)

    if not dry_run_bool and not confirm_bool:
        raise ValueError(
            "This operation requires confirm=True to execute. "
            "Use dry_run=True to preview changes first."
        )

    # Validate overrides up-front so we fail fast before hitting the API.
    action_upper: str | None = None
    if action is not None:
        action_upper = action.upper()
        if action_upper not in ("ALLOW", "BLOCK"):
            raise ValueError(f"Invalid action '{action}'. Must be ALLOW or BLOCK.")

    ip_version_upper: str | None = None
    if ip_version is not None:
        ip_version_upper = ip_version.upper()
        if ip_version_upper not in _VALID_IP_VERSIONS:
            raise ValueError(
                f"Invalid ip_version '{ip_version}'. Must be one of: {list(_VALID_IP_VERSIONS)}"
            )

    # Collect overrides so we can both preview them (dry_run) and merge them.
    overrides: dict[str, Any] = {}
    if name is not None:
        overrides["name"] = name
    if action_upper is not None:
        overrides["action"] = action_upper
    if enabled is not None:
        overrides["enabled"] = enabled
    if logging is not None:
        overrides["logging"] = logging
    if ip_version_upper is not None:
        overrides["ip_version"] = ip_version_upper
    if protocol is not None:
        overrides["protocol"] = protocol
    if description is not None:
        overrides["description"] = description

    async with UniFiClient(settings) as client:
        logger.info(
            sanitize_log_message(
                f"Updating firewall policy {policy_id} for site {site_id}"
            )
        )

        if not client.is_authenticated:
            await client.authenticate()

        endpoint = f"{settings.get_v2_api_path(site_id)}/firewall-policies/{policy_id}"

        # Fetch the existing policy so we can merge + PUT the full object.
        try:
            current_response = await client.get(endpoint)
        except ResourceNotFoundError as err:
            raise ResourceNotFoundError("firewall_policy", policy_id) from err

        current = (
            current_response.get("data", current_response)
            if isinstance(current_response, dict)
            else current_response
        )
        if not current or not isinstance(current, dict):
            raise ResourceNotFoundError("firewall_policy", policy_id)

        if current.get("predefined"):
            raise ValueError(
                f"Cannot update predefined system rule '{current.get('name', policy_id)}'."
            )

        merged = {**current, **overrides}
        # Strip fields the API controls; sending them back causes validation errors.
        for field in ("_id", "predefined"):
            merged.pop(field, None)

        if dry_run_bool:
            logger.info(
                sanitize_log_message(
                    f"DRY RUN: Would update firewall policy {policy_id}"
                )
            )
            return {
                "status": "dry_run",
                "policy_id": policy_id,
                "changes": overrides,
                "merged_payload": merged,
            }

        try:
            response = await client.put(endpoint, json_data=merged)
        except ResourceNotFoundError as err:
            raise ResourceNotFoundError("firewall_policy", policy_id) from err

        data = (
            response.get("data", response) if isinstance(response, dict) else response
        )

        logger.info(sanitize_log_message(f"Updated firewall policy {policy_id}"))
        log_audit(
            operation="update_firewall_policy",
            parameters={"policy_id": policy_id, "site_id": site_id, **overrides},
            result="success",
            site_id=site_id,
        )

        return FirewallPolicy(**data).model_dump()


async def delete_firewall_policy(
    policy_id: str,
    site_id: str = "default",
    settings: Settings = None,
    confirm: bool | str = False,
    dry_run: bool | str = False,
) -> dict[str, Any]:
    """Delete a firewall policy.

    Warning: Cannot delete predefined system rules.

    Args:
        policy_id: ID of policy to delete
        site_id: Site identifier
        settings: Application settings
        confirm: REQUIRED True for destructive operations
        dry_run: Preview deletion without applying

    Returns:
        Confirmation of deletion

    Raises:
        NotImplementedError: When using cloud API (v2 endpoints require local access)
        ValueError: If confirmation not provided or attempting to delete predefined rule
        ResourceNotFoundError: If policy not found
    """
    _ensure_local_api(settings)

    if not coerce_bool(dry_run) and not coerce_bool(confirm):
        raise ValueError("This operation deletes a firewall policy. Pass confirm=True to proceed.")

    async with UniFiClient(settings) as client:
        logger.info(sanitize_log_message(f"Deleting firewall policy {policy_id} from site {site_id}"))

        if not client.is_authenticated:
            await client.authenticate()

        endpoint = f"{settings.get_v2_api_path(site_id)}/firewall-policies/{policy_id}"

        try:
            policy_response = await client.get(endpoint)
        except ResourceNotFoundError as err:
            raise ResourceNotFoundError("firewall_policy", policy_id) from err

        if isinstance(policy_response, dict) and "data" in policy_response:
            policy_data = policy_response["data"]
        else:
            policy_data = policy_response

        if not policy_data:
            raise ResourceNotFoundError("firewall_policy", policy_id)

        policy = FirewallPolicy(**policy_data)

        if policy.predefined:
            raise ValueError(
                f"Cannot delete predefined system rule '{policy.name}' (id={policy_id}). "
                "Predefined rules are managed by the UniFi system."
            )

        if dry_run:
            logger.info(sanitize_log_message(f"DRY RUN: Would delete firewall policy {policy_id}"))
            return {
                "status": "dry_run",
                "policy_id": policy_id,
                "action": "would_delete",
                "policy": policy.model_dump(),
            }

        await client.delete(endpoint)

        log_audit(
            operation="delete_firewall_policy",
            parameters={"policy_id": policy_id, "site_id": site_id},
            result="success",
            site_id=site_id,
        )

        logger.info(sanitize_log_message(f"Deleted firewall policy {policy_id} from site {site_id}"))

        return {
            "status": "success",
            "policy_id": policy_id,
            "action": "deleted",
        }
