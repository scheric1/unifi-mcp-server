# UniFi MCP Server Development Plan

**Document Version:** 2026-04-23
**API Target:** UniFi Network v10.3.55 + Site Manager v1.0.0 + Protect v6.2.83
**Current Codebase:** ~200 async tool functions across 37 modules

---

## 1. Executive Summary

This plan maps the path from the current implementation (~200 tools) to full API code coverage against the documented UniFi API surface. The current server covers the majority of Network API endpoints, a subset of Site Manager endpoints, and zero Protect endpoints.

**Immediate priority** is closing the remaining Network API gaps, completing Site Manager coverage, and implementing the documented Protect API. The plan is organized into four execution phases with clear deliverables and acceptance criteria.

---

## 2. Current State

### 2.1 Implemented (✅)

| API Area | Status | Tool Count | Notes |
|----------|--------|------------|-------|
| **Devices** | Complete | ~10 | CRUD, adoption, port actions, statistics, pending devices |
| **Clients** | Complete | ~8 | List, details, search, block/unblock, reconnect, DPI |
| **Networks** | Complete | ~8 | VLANs, WAN, corporate, VPN networks; full CRUD |
| **WiFi / WLANs** | Complete | ~6 | SSID CRUD, statistics, radio config |
| **Firewall Zones** | Complete | ~10 | Zone CRUD, assignment, policies, matrix (read-only where API limits) |
| **Firewall Policies** | Complete | ~8 | Policy CRUD, ordering, patch |
| **ACL Rules** | Complete | ~6 | ACL CRUD, ordering |
| **Firewall Groups** | Complete | ~6 | Address/port group CRUD |
| **Traffic Flows** | Complete | ~15 | Real-time flows, filtering, analytics, blocking, export |
| **DPI** | Complete | ~5 | Statistics, top applications, client DPI, categories, applications |
| **QoS** | Complete | ~12 | QoS profiles, ProAV templates, Smart Queue, traffic routes, DSCP |
| **Traffic Matching Lists** | Complete | ~5 | CRUD operations |
| **Port Forwarding** | Complete | ~5 | CRUD |
| **Port Profiles** | Complete | ~6 | CRUD with overrides |
| **RADIUS** | Complete | ~10 | Profile CRUD, account CRUD |
| **Guest Portal / Hotspot** | Complete | ~8 | Portal config, packages, vouchers |
| **Backups** | Complete | ~11 | Trigger, list, download, delete, restore, validate, schedule |
| **Topology** | Complete | ~5 | Graph data, connections, port mappings, export, statistics |
| **Site VPN** | Complete | ~4 | Site-to-site tunnels, server list |
| **WAN / DNS** | Complete | ~6 | Connections, DNS, content filtering |
| **DHCP Reservations** | Complete | ~5 | CRUD |
| **Site Manager (partial)** | Partial | ~15 | Aggregated sites, health, inventory, ISP metrics, SD-WAN, hosts, version control |
| **Device Control** | Complete | ~6 | Upgrade, restart, locate, LED |

**Total implemented:** ~194 async tool functions.

### 2.2 Known Limitations

- **ZBF Matrix policies:** Read-only / limited due to API endpoint unavailability on real hardware. Verified on UDM Pro v10.0.156+. See `docs/archive/ZBF_STATUS.md`.
- **Cloud Connector proxy:** Not yet implemented (requires separate auth flow research).
- **Protect API:** Zero coverage (documented but not coded).

---

## 3. Gap Analysis

Based on `docs/UNIFI_API.md` (v10.3.55) and `API.md`.

### 3.1 Critical Gaps (Blocking Full Coverage)

| # | Gap | API Version | Endpoints | Impact |
|---|-----|-------------|-----------|--------|
| G1 | **Protect API** | v6.2.83 | 36+ endpoints (cameras, lights, sensors, chimes, NVR, RTSPS, PTZ, talkback, live views, events) | Largest single gap. Fully documented, zero code. |
| G2 | **Switching API** | v10.3.55 | Switch Stacks, MC-LAG Domains, LAGs | Documented in UNIFI_API.md, no tools. |
| G3 | **Network References** | v10.3.55 | `/api/s/{site}/rest/networkref` | Small gap, used for network dependency mapping. |
| G4 | **Cloud Connector** | v1.0.0 | Network + Protect proxy endpoints (POST/GET/PUT/DELETE/PATCH) | Enables remote cloud management without direct local access. |

### 3.2 Minor Gaps

| # | Gap | Notes |
|---|-----|-------|
| G5 | **Speed Test** | Endpoints exist (`/cmd/devmgr/speedtest`, `/cmd/devmgr/speedtest-status`) but not implemented. Low user demand. |
| G6 | **Spectrum Scan** | `/stat/spectrumscan` for RF analysis. Low priority. |
| G7 | **Dynamic DNS full CRUD** | GET exists; PUT/POST/DELETE for custom providers missing. |
| G8 | **Tagged MAC Management** | `/rest/tag` endpoints. Low priority. |
| G9 | **Device Migration** | `/cmd/devmgr/migrate`, `/cmd/devmgr/cancel-migrate`. Low priority. |

---

## 4. Phased Implementation Plan

### Phase 1: Network API Completion (Target: 2-3 weeks)

**Goal:** Close all remaining Network API v10.3.55 gaps.

#### 1.1 Switching API

- `list_switch_stacks` / `get_switch_stack`
- `list_mclag_domains` / `get_mclag_domain`
- `list_lags` / `get_lag_details`
- Data models: `SwitchStack`, `MclagDomain`, `Lag`, `LagMember`
- Estimated tools: 6
- Acceptance: integration tests against real or mock stack topology

#### 1.2 Network References

- `get_network_references(site_id, network_id)`
- Returns upstream/downstream network dependencies
- Estimated tools: 1
- Acceptance: returns valid reference graph for a corporate network

#### 1.3 Speed Test & Spectrum (Stretch)

- `run_speed_test`, `get_speed_test_status`, `get_speed_test_history`
- `get_spectrum_scan`, `list_spectrum_interference`
- Estimated tools: 4-5
- Acceptance: dry-run safe; speed test triggers real traffic (document clearly)

**Phase 1 Deliverables:**

- [ ] `src/tools/switching.py` with full Switching API coverage
- [ ] `src/models/switching.py` data models
- [ ] Network references tool in `src/tools/networks.py` or new module
- [ ] Integration tests for switching and references
- [ ] `API.md` and `UNIFI_API.md` updated with ✅ marks

---

### Phase 2: Site Manager API Completion (Target: 1-2 weeks)

**Goal:** Complete Site Manager v1.0.0 coverage and add Cloud Connector foundation.

#### 2.1 Connector Proxy — Network

- `connector_network_post`, `connector_network_get`, `connector_network_put`, `connector_network_delete`, `connector_network_patch`
- Generic wrapper tools that proxy arbitrary requests through `api.ui.com/v1/connector/...`
- Requires `console_id`, `site_id`, and path/body parameters
- Estimated tools: 5

#### 2.2 Connector Proxy — Protect

- `connector_protect_post`, `connector_protect_get`, `connector_protect_put`, `connector_protect_delete`, `connector_protect_patch`
- Same pattern as Network connector
- Estimated tools: 5

**Phase 2 Deliverables:**

- [ ] `src/tools/connector.py` with Network and Protect proxy tools
- [ ] `src/models/connector.py` request/response wrappers
- [ ] Documentation: connector auth flow and usage examples
- [ ] Integration tests (mocked cloud responses)

---

### Phase 3: Protect API Integration (Target: 4-6 weeks)

**Goal:** Full Protect v6.2.83 API coverage — the largest single expansion.

This is a new application domain requiring:

- New API client context (`src/api/protect_client.py`) or extension of existing client
- New models (`src/models/protect_*.py`)
- New tool modules (`src/tools/protect_*.py`)
- New resources (`src/resources/protect.py`)

#### 3.1 Core Protect Infrastructure

- Protect API client with NVR base URL discovery
- Authentication reuse (local API key / cloud connector)
- Response normalization for Protect-specific wrappers

#### 3.2 Camera Management

- `list_cameras`, `get_camera`, `update_camera`, `get_camera_snapshot`
- `create_camera_rtsps_stream`, `delete_camera_rtsps_stream`, `get_camera_rtsps_streams`
- `disable_camera_microphone`
- `create_camera_talkback_session`
- `start_camera_ptz_patrol`, `stop_camera_ptz_patrol`, `move_camera_ptz_preset`
- Estimated tools: 12

#### 3.3 Light, Sensor, Chime Management

- `list_lights`, `get_light`, `update_light`
- `list_sensors`, `get_sensor`, `update_sensor`
- `list_chimes`, `get_chime`, `update_chime`
- Estimated tools: 9

#### 3.4 NVR & Device Assets

- `get_nvr_details`
- `upload_device_asset_file`, `get_device_asset_files`
- Estimated tools: 3

#### 3.5 Live Views & Viewer Config

- `get_viewer_details`, `update_viewer_settings`, `list_viewers`
- `get_live_view`, `update_live_view`, `list_live_views`, `create_live_view`
- Estimated tools: 7

#### 3.6 Events & Webhooks

- `get_protect_events`
- `send_alarm_manager_webhook`
- Estimated tools: 2

#### 3.7 Device Updates

- `get_device_update_messages`
- Estimated tools: 1

**Phase 3 Deliverables:**

- [ ] `src/api/protect_client.py` — Protect-specific HTTP client
- [ ] `src/models/protect_*.py` — Camera, Light, Sensor, Chime, NVR, LiveView, Viewer models
- [ ] `src/tools/protect_cameras.py` — Camera + PTZ + RTSPS + talkback
- [ ] `src/tools/protect_devices.py` — Lights, sensors, chimes
- [ ] `src/tools/protect_nvr.py` — NVR and asset files
- [ ] `src/tools/protect_views.py` — Live views and viewer config
- [ ] `src/tools/protect_events.py` — Events and alarm webhooks
- [ ] `src/resources/protect.py` — MCP resources for cameras, events
- [ ] Integration test suite for Protect (mocked NVR responses)
- [ ] `API.md` updated with Protect tool reference
- [ ] `UNIFI_API.md` Protect section annotated with ✅

**Estimated new tools for Phase 3:** 34-36

---

### Phase 4: Testing, Polish, and Minor Gaps (Target: 2-3 weeks)

**Goal:** Reach 80%+ test coverage, close minor gaps, and production-harden.

#### 4.1 Minor Gap Closure

- Dynamic DNS full CRUD (`src/tools/wans.py` extension)
- Tagged MAC management (`src/tools/devices.py` extension or new module)
- Device migration tools
- Spectrum scan (if not done in Phase 1)

#### 4.2 Test Coverage

- Unit tests for all new Phase 1-3 modules
- Integration tests for Switching, Connector, Protect
- Target: 80%+ overall coverage (currently ~84% on core modules)

#### 4.3 Documentation

- `API.md`: complete tool reference for all new tools
- `UNIFI_API.md`: mark every implemented endpoint with ✅
- `README.md`: update feature matrix and tool count
- `CHANGELOG.md`: version entry

#### 4.4 Release Preparation

- Version bump to v0.2.0 (or appropriate version)
- Pre-commit hooks pass (`ruff`, `mypy`, `bandit`)
- Docker build verification
- Security scan clean

**Phase 4 Deliverables:**

- [ ] All new code covered by tests
- [ ] Documentation fully synchronized with code
- [ ] CI green
- [ ] Release tag ready

---

## 5. Version Roadmap

| Version | Scope | New Tools | Cumulative | Timeline |
|---------|-------|-----------|------------|----------|
| **v0.1.x** | Current | ~194 | ~194 | Now |
| **v0.2.0** | Phase 1 + Phase 2 + Phase 4 minor gaps | ~25-30 | ~220-225 | Q2 2026 |
| **v0.3.0** | Phase 3 — Protect API | ~35-40 | ~255-265 | Q3 2026 |
| **v1.0.0** | Multi-application platform, enterprise features | TBD | 300+ | H2 2026 |

---

## 6. Endpoint Inventory

### Fully Implemented ✅

All endpoints below have corresponding MCP tools and models.

- `/api/s/{site}/stat/device` — Devices
- `/api/s/{site}/rest/device` — Device management
- `/api/s/{site}/stat/sta` — Clients
- `/api/s/{site}/rest/user` — Client management
- `/api/s/{site}/rest/networkconf` — Networks
- `/api/s/{site}/rest/wlanconf` — WiFi
- `/api/s/{site}/rest/firewallzone` — Firewall zones
- `/api/s/{site}/rest/firewallrule` / `firewallpolicy` — Firewall policies
- `/api/s/{site}/rest/firewallgroup` — Firewall groups
- `/api/s/{site}/rest/radiusprofile` / `account` — RADIUS
- `/api/s/{site}/rest/hotspotpackage` — Hotspot
- `/api/s/{site}/cmd/hotspot` — Vouchers
- `/api/s/{site}/rest/portforward` — Port forwarding
- `/api/s/{site}/rest/portconf` — Port profiles
- `/api/s/{site}/rest/dhcpgroup` / `dhcpd` — DHCP reservations
- `/api/s/{site}/rest/trafficroute` / `qosprofile` — QoS
- `/api/s/{site}/rest/trafficmatch` — Traffic matching lists
- `/api/s/{site}/stat/trafficflow` / `rest/trafficflow` — Traffic flows
- `/api/s/{site}/stat/dpi` — DPI statistics
- `/api/s/{site}/stat/topology` — Topology
- `/api/cmd/backup` / `/api/backup/...` — Backups
- `/api/s/{site}/rest/wanconf` / `rest/dnsfilter` — WAN/DNS
- `/api/s/{site}/rest/vpntunnel` — Site-to-site VPN
- Site Manager v1: aggregated sites, health, inventory, ISP metrics, SD-WAN, hosts

### Partially Implemented ⚠️

| Endpoint | Status | Missing |
|----------|--------|---------|
| `/api/s/{site}/rest/dynamicdns` | GET only | PUT/POST/DELETE |
| `/api/s/{site}/rest/firewallzonematrix` | Read-only | Advanced matrix mutations (API-limited on hardware) |

### Not Implemented ❌

| Endpoint | Category | Planned Phase |
|----------|----------|---------------|
| `/api/s/{site}/rest/switchstack` | Switching | Phase 1 |
| `/api/s/{site}/rest/mclagdomain` | Switching | Phase 1 |
| `/api/s/{site}/rest/lag` | Switching | Phase 1 |
| `/api/s/{site}/rest/networkref` | Networks | Phase 1 |
| `/api/s/{site}/cmd/devmgr/speedtest` | Diagnostics | Phase 1 (stretch) |
| `/api/s/{site}/stat/spectrumscan` | RF | Phase 4 |
| `/v1/connector/.../proxy/network/...` | Site Manager | Phase 2 |
| `/v1/connector/.../proxy/protect/...` | Site Manager | Phase 2 |
| Protect v6.2.83 endpoints (36+) | Protect | Phase 3 |
| `/api/s/{site}/rest/tag` | Devices | Phase 4 |
| `/api/s/{site}/cmd/devmgr/migrate` | Devices | Phase 4 |

---

## 7. Technical Architecture Notes

### 7.1 New Modules Required

```
src/
  api/
    protect_client.py      # Phase 3
  models/
    switching.py           # Phase 1
    protect_camera.py      # Phase 3
    protect_light.py       # Phase 3
    protect_sensor.py      # Phase 3
    protect_chime.py       # Phase 3
    protect_nvr.py         # Phase 3
    protect_liveview.py    # Phase 3
    connector.py           # Phase 2
  tools/
    switching.py           # Phase 1
    connector.py           # Phase 2
    protect_cameras.py     # Phase 3
    protect_devices.py     # Phase 3
    protect_nvr.py         # Phase 3
    protect_views.py       # Phase 3
    protect_events.py      # Phase 3
  resources/
    protect.py             # Phase 3
```

### 7.2 Data Model Patterns

All new models follow the existing Pydantic v2 pattern:

```python
from pydantic import BaseModel, Field
from typing import Literal

class SwitchStack(BaseModel):
    id: str = Field(alias="_id")
    name: str
    model: str
    member_ports: list[str]
    enabled: bool = True
```

### 7.3 Tool Registration

New tool modules are auto-registered via `register_module_tools()` in `src/main.py`. After creating a new module, add the import and registration call:

```python
from .tools import switching as switching_tools
# ...
register_module_tools(mcp, switching_tools, settings)
```

---

## 8. Testing & Quality Targets

| Metric | Current | Phase 1 Target | Phase 3 Target |
|--------|---------|----------------|----------------|
| Unit test coverage | ~84% (core) | 85% | 80%+ overall |
| Integration tests | 12 suites | +2 (switching, connector) | +1 (protect) |
| Lint (ruff) | Pass | Pass | Pass |
| Type check (mypy) | Pass | Pass | Pass |
| Security (bandit) | Pass | Pass | Pass |

---

## 9. Documentation Maintenance

After each phase:

1. Update `docs/UNIFI_API.md` — add ✅ to implemented endpoints
2. Update `API.md` — add new MCP tools to reference tables
3. Update `README.md` — refresh feature matrix and tool count
4. Update `CHANGELOG.md` — version entry with phase summary

---

## 10. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Protect API endpoints differ from docs | Medium | High | Verify against real NVR early in Phase 3; maintain fallback wrappers |
| Switching endpoints unavailable on test hardware | Medium | Medium | Use mock responses for CI; manual validation on physical stack |
| Cloud Connector requires OAuth changes | Low | Medium | Research auth flow before Phase 2; fallback to API-key proxy if possible |
| Test coverage drops below threshold | Low | Medium | Gate PRs on coverage; add tests before merging features |

---

*Plan maintained by: Hermes / AI coding agents*
*Last updated: 2026-04-23*
*Next review: Phase 1 completion*
