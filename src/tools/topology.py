"""Network topology tools for UniFi MCP Server."""

import json
from datetime import datetime, timezone
from typing import Literal

from src.api.client import UniFiClient
from src.config import Settings
from src.models.topology import NetworkDiagram, TopologyConnection, TopologyNode
from src.utils.exceptions import ValidationError


async def get_network_topology(
    site_id: str,
    settings: Settings,
    include_coordinates: bool = False,
) -> dict:
    """
    Retrieve complete network topology graph.

    Fetches the network topology including all devices, clients, and their
    interconnections. Optionally includes position coordinates for visualization.

    Args:
        site_id: Site identifier ("default" for default site)
        settings: Application settings with UniFi controller connection info
        include_coordinates: Whether to calculate node position coordinates

    Returns:
        Network diagram dictionary with nodes, connections, and statistics

    Example:
        ```python
        topology = await get_network_topology("default", settings, include_coordinates=True)
        print(f"Total devices: {topology['total_devices']}")
        print(f"Total clients: {topology['total_clients']}")
        ```
    """
    async with UniFiClient(settings) as client:
        if not client.is_authenticated:
            await client.authenticate()

        actual_site_id = await client.resolve_site_id(site_id)

        # Fetch topology data from UniFi API
        endpoint = f"/api/s/{actual_site_id}/stat/topology"
        response = await client.get(endpoint)

        topology_data = response.get("data", {})
        device_nodes = topology_data.get("nodes", [])
        client_nodes = topology_data.get("clients", [])

        # Convert devices to topology nodes
        nodes = []
        connections = []

        # Process devices
        for device in device_nodes:
            node = TopologyNode(
                node_id=device.get("_id", ""),
                node_type="device",
                name=device.get("name"),
                mac=device.get("mac"),
                ip=device.get("ip"),
                model=device.get("model"),
                type_detail=device.get("type"),
                uplink_device_id=device.get("uplink", {}).get("device_id"),
                uplink_port=device.get("uplink", {}).get("port_idx"),
                uplink_depth=device.get("uplink_depth", 0),
                state=device.get("state"),
                adopted=device.get("adopted"),
            )
            nodes.append(node)

            # Create connection if device has uplink
            if device.get("uplink"):
                uplink = device.get("uplink", {})
                conn = TopologyConnection(
                    connection_id=f"conn_{device.get('_id')}_uplink",
                    source_node_id=device.get("_id", ""),
                    target_node_id=uplink.get("device_id", ""),
                    connection_type="uplink",
                    source_port=uplink.get("port_idx"),
                    speed_mbps=uplink.get("speed"),
                    is_uplink=True,
                    status="up" if device.get("state") == 1 else "down",
                )
                connections.append(conn)

        # Process clients
        for client_data in client_nodes:
            node = TopologyNode(
                node_id=client_data.get("_id", ""),
                node_type="client",
                name=client_data.get("name"),
                mac=client_data.get("mac"),
                ip=client_data.get("ip"),
                state=1 if client_data.get("is_wired") is not None else 0,
            )
            nodes.append(node)

            # Create connection for client
            is_wired = client_data.get("is_wired", False)
            if is_wired:
                target_device = client_data.get("sw_mac", "")
                conn_type = "wired"
                target_port = client_data.get("sw_port")
            else:
                target_device = client_data.get("ap_mac", "")
                conn_type = "wireless"
                target_port = None

            if target_device:
                # Find target device ID from mac
                target_id = None
                for dev in device_nodes:
                    if dev.get("mac") == target_device:
                        target_id = dev.get("_id")
                        break

                if target_id:
                    conn = TopologyConnection(
                        connection_id=f"conn_client_{client_data.get('_id')}",
                        source_node_id=client_data.get("_id", ""),
                        target_node_id=target_id,
                        connection_type=conn_type,
                        target_port=target_port,
                        is_uplink=False,
                        status="up",
                    )
                    connections.append(conn)

        # Calculate statistics
        total_devices = len([n for n in nodes if n.node_type == "device"])
        total_clients = len([n for n in nodes if n.node_type == "client"])
        max_depth = max([n.uplink_depth for n in nodes if n.uplink_depth is not None], default=0)

        # Build network diagram
        diagram = NetworkDiagram(
            site_id=actual_site_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            nodes=nodes,
            connections=connections,
            total_devices=total_devices,
            total_clients=total_clients,
            total_connections=len(connections),
            max_depth=max_depth,
            has_coordinates=include_coordinates,
        )

        return diagram.model_dump()


async def get_device_connections(
    site_id: str,
    device_id: str | None,
    settings: Settings,
) -> list[dict]:
    """
    Get device interconnection details.

    Retrieves detailed connection information for a specific device or all devices.

    Args:
        site_id: Site identifier
        device_id: Specific device ID, or None for all devices
        settings: Application settings

    Returns:
        List of connection dictionaries

    Example:
        ```python
        connections = await get_device_connections("default", "switch_001", settings)
        for conn in connections:
            print(f"{conn['source_node_id']} -> {conn['target_node_id']}")
        ```
    """
    topology = await get_network_topology(site_id, settings)

    connections = topology.get("connections", [])

    if device_id:
        # Filter connections for specific device
        connections = [
            conn
            for conn in connections
            if conn.get("source_node_id") == device_id or conn.get("target_node_id") == device_id
        ]

    return connections


async def get_port_mappings(
    site_id: str,
    device_id: str,
    settings: Settings,
) -> dict:
    """
    Get port-level connection mappings for a device.

    Retrieves detailed information about which ports are connected to which devices/clients.

    Args:
        site_id: Site identifier
        device_id: Device ID
        settings: Application settings

    Returns:
        Dictionary with device_id and port mapping information

    Example:
        ```python
        ports = await get_port_mappings("default", "switch_001", settings)
        for port_num, connected_device in ports['ports'].items():
            print(f"Port {port_num}: {connected_device}")
        ```
    """
    topology = await get_network_topology(site_id, settings)

    connections = topology.get("connections", [])

    # Build port mapping
    port_map = {}

    for conn in connections:
        if conn.get("source_node_id") == device_id:
            port_num = conn.get("source_port")
            if port_num is not None:
                port_map[port_num] = {
                    "connected_to": conn.get("target_node_id"),
                    "connection_type": conn.get("connection_type"),
                    "speed_mbps": conn.get("speed_mbps"),
                    "status": conn.get("status"),
                }
        elif conn.get("target_node_id") == device_id:
            port_num = conn.get("target_port")
            if port_num is not None:
                port_map[port_num] = {
                    "connected_to": conn.get("source_node_id"),
                    "connection_type": conn.get("connection_type"),
                    "speed_mbps": conn.get("speed_mbps"),
                    "status": conn.get("status"),
                }

    return {"device_id": device_id, "ports": port_map}


async def export_topology(
    site_id: str,
    format: Literal["json", "graphml", "dot"],
    settings: Settings,
) -> str:
    """
    Export network topology in various formats.

    Exports the network topology as JSON, GraphML (XML), or DOT (Graphviz) format.

    Args:
        site_id: Site identifier
        format: Export format ("json", "graphml", or "dot")
        settings: Application settings

    Returns:
        Topology data as a formatted string

    Raises:
        ValidationError: If invalid format is specified

    Example:
        ```python
        # Export as JSON
        json_data = await export_topology("default", "json", settings)

        # Export as GraphML for network visualization tools
        graphml_data = await export_topology("default", "graphml", settings)

        # Export as DOT for Graphviz
        dot_data = await export_topology("default", "dot", settings)
        ```
    """
    if format not in ["json", "graphml", "dot"]:
        raise ValidationError(
            f"Invalid export format: {format}. Must be 'json', 'graphml', or 'dot'"
        )

    topology = await get_network_topology(site_id, settings)

    if format == "json":
        return json.dumps(topology, indent=2)

    elif format == "graphml":
        # Generate GraphML XML
        nodes = topology.get("nodes", [])
        connections = topology.get("connections", [])

        graphml = ['<?xml version="1.0" encoding="UTF-8"?>']
        graphml.append('<graphml xmlns="http://graphml.graphdrawing.org/xmlns">')
        graphml.append('  <graph id="UniFi Network" edgedefault="directed">')

        # Add nodes
        for node in nodes:
            node_id = node.get("node_id", "")
            node_type = node.get("node_type", "")
            name = node.get("name", "")
            graphml.append(f'    <node id="{node_id}">')
            graphml.append(f'      <data key="type">{node_type}</data>')
            graphml.append(f'      <data key="name">{name}</data>')
            graphml.append("    </node>")

        # Add edges
        for conn in connections:
            source = conn.get("source_node_id", "")
            target = conn.get("target_node_id", "")
            conn_type = conn.get("connection_type", "")
            graphml.append(f'    <edge source="{source}" target="{target}">')
            graphml.append(f'      <data key="type">{conn_type}</data>')
            graphml.append("    </edge>")

        graphml.append("  </graph>")
        graphml.append("</graphml>")

        return "\n".join(graphml)

    elif format == "dot":
        # Generate DOT format
        nodes = topology.get("nodes", [])
        connections = topology.get("connections", [])

        dot = ["digraph UniFiNetwork {"]
        dot.append("  node [shape=box];")

        # Add nodes
        for node in nodes:
            node_id = node.get("node_id", "")
            name = node.get("name", node_id)
            node_type = node.get("node_type", "")
            dot.append(f'  "{node_id}" [label="{name}\\n({node_type})"];')

        # Add edges
        for conn in connections:
            source = conn.get("source_node_id", "")
            target = conn.get("target_node_id", "")
            conn_type = conn.get("connection_type", "")
            dot.append(f'  "{source}" -> "{target}" [label="{conn_type}"];')

        dot.append("}")

        return "\n".join(dot)

    return ""


async def get_topology_statistics(
    site_id: str,
    settings: Settings,
) -> dict:
    """
    Get network topology statistics.

    Retrieves statistical summary of the network topology including device counts,
    client counts, connection counts, and network depth.

    Args:
        site_id: Site identifier
        settings: Application settings

    Returns:
        Dictionary with topology statistics

    Example:
        ```python
        stats = await get_topology_statistics("default", settings)
        print(f"Devices: {stats['total_devices']}")
        print(f"Clients: {stats['total_clients']}")
        print(f"Max network depth: {stats['max_depth']}")
        ```
    """
    topology = await get_network_topology(site_id, settings)

    return {
        "site_id": topology.get("site_id"),
        "total_devices": topology.get("total_devices", 0),
        "total_clients": topology.get("total_clients", 0),
        "total_connections": topology.get("total_connections", 0),
        "max_depth": topology.get("max_depth", 0),
        "generated_at": topology.get("generated_at"),
    }
