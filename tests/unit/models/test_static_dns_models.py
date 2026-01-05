"""Tests for Static DNS models."""

import pytest
from pydantic import ValidationError

from src.models.static_dns import (
    StaticDNSCreate,
    StaticDNSDevice,
    StaticDNSDevicesResponse,
    StaticDNSEntry,
    StaticDNSListResponse,
)


class TestStaticDNSEntry:
    """Tests for StaticDNSEntry model."""

    def test_minimal_entry(self):
        entry = StaticDNSEntry(
            _id="dns123",
            hostname="server.local",
            ipAddress="192.168.1.100",
        )
        assert entry.id == "dns123"
        assert entry.hostname == "server.local"
        assert entry.ip_address == "192.168.1.100"
        assert entry.enabled is True
        assert entry.description is None

    def test_full_entry(self):
        entry = StaticDNSEntry(
            _id="dns456",
            hostname="nas.home",
            ipAddress="10.0.0.50",
            enabled=False,
            description="NAS Server",
            siteId="site001",
        )
        assert entry.id == "dns456"
        assert entry.hostname == "nas.home"
        assert entry.ip_address == "10.0.0.50"
        assert entry.enabled is False
        assert entry.description == "NAS Server"
        assert entry.site_id == "site001"

    def test_alias_access(self):
        entry = StaticDNSEntry(
            _id="dns789",
            hostname="printer.office",
            ipAddress="172.16.0.25",
        )
        assert entry.id == "dns789"
        assert entry.ip_address == "172.16.0.25"

    def test_extra_fields_allowed(self):
        entry = StaticDNSEntry(
            _id="dns999",
            hostname="custom.local",
            ipAddress="192.168.1.1",
            unknown_field="allowed",
        )
        assert entry.id == "dns999"

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            StaticDNSEntry(hostname="test.local")

    def test_dict_export(self):
        entry = StaticDNSEntry(
            _id="dns123",
            hostname="server.local",
            ipAddress="192.168.1.100",
        )
        data = entry.model_dump(by_alias=True)
        assert data["_id"] == "dns123"
        assert data["ipAddress"] == "192.168.1.100"


class TestStaticDNSDevice:
    """Tests for StaticDNSDevice model."""

    def test_minimal_device(self):
        device = StaticDNSDevice(mac="aa:bb:cc:dd:ee:ff")
        assert device.mac == "aa:bb:cc:dd:ee:ff"
        assert device.hostname is None
        assert device.ip_address is None
        assert device.use_fixed_ip is False

    def test_full_device(self):
        device = StaticDNSDevice(
            mac="11:22:33:44:55:66",
            hostname="workstation",
            ipAddress="192.168.1.50",
            name="John's PC",
            useFixedIp=True,
        )
        assert device.mac == "11:22:33:44:55:66"
        assert device.hostname == "workstation"
        assert device.ip_address == "192.168.1.50"
        assert device.name == "John's PC"
        assert device.use_fixed_ip is True

    def test_alias_access(self):
        device = StaticDNSDevice(
            mac="aa:bb:cc:dd:ee:ff",
            ipAddress="10.0.0.1",
            useFixedIp=True,
        )
        assert device.ip_address == "10.0.0.1"
        assert device.use_fixed_ip is True

    def test_extra_fields_allowed(self):
        device = StaticDNSDevice(
            mac="aa:bb:cc:dd:ee:ff",
            vendor="Dell",
        )
        assert device.mac == "aa:bb:cc:dd:ee:ff"


class TestStaticDNSCreate:
    """Tests for StaticDNSCreate model."""

    def test_minimal_create(self):
        create = StaticDNSCreate(
            hostname="newserver.local",
            ipAddress="192.168.1.200",
        )
        assert create.hostname == "newserver.local"
        assert create.ip_address == "192.168.1.200"
        assert create.enabled is True
        assert create.description is None

    def test_full_create(self):
        create = StaticDNSCreate(
            hostname="database.internal",
            ipAddress="10.0.0.100",
            enabled=False,
            description="Production database",
        )
        assert create.hostname == "database.internal"
        assert create.ip_address == "10.0.0.100"
        assert create.enabled is False
        assert create.description == "Production database"

    def test_hostname_min_length(self):
        with pytest.raises(ValidationError) as exc_info:
            StaticDNSCreate(hostname="", ipAddress="192.168.1.1")
        assert "hostname" in str(exc_info.value).lower()

    def test_hostname_max_length(self):
        long_hostname = "a" * 254
        with pytest.raises(ValidationError) as exc_info:
            StaticDNSCreate(hostname=long_hostname, ipAddress="192.168.1.1")
        assert "hostname" in str(exc_info.value).lower()

    def test_description_max_length(self):
        long_desc = "x" * 257
        with pytest.raises(ValidationError) as exc_info:
            StaticDNSCreate(
                hostname="test.local",
                ipAddress="192.168.1.1",
                description=long_desc,
            )
        assert "description" in str(exc_info.value).lower()

    def test_valid_max_hostname(self):
        max_hostname = "a" * 253
        create = StaticDNSCreate(hostname=max_hostname, ipAddress="192.168.1.1")
        assert len(create.hostname) == 253

    def test_valid_max_description(self):
        max_desc = "x" * 256
        create = StaticDNSCreate(
            hostname="test.local",
            ipAddress="192.168.1.1",
            description=max_desc,
        )
        assert len(create.description) == 256


class TestStaticDNSListResponse:
    """Tests for StaticDNSListResponse model."""

    def test_empty_response(self):
        response = StaticDNSListResponse()
        assert response.entries == []
        assert response.total == 0

    def test_with_entries(self):
        entry1 = StaticDNSEntry(
            _id="dns1",
            hostname="server1.local",
            ipAddress="192.168.1.1",
        )
        entry2 = StaticDNSEntry(
            _id="dns2",
            hostname="server2.local",
            ipAddress="192.168.1.2",
        )
        response = StaticDNSListResponse(entries=[entry1, entry2], total=2)
        assert len(response.entries) == 2
        assert response.total == 2
        assert response.entries[0].hostname == "server1.local"

    def test_from_dict(self):
        data = {
            "entries": [{"_id": "dns1", "hostname": "test.local", "ipAddress": "10.0.0.1"}],
            "total": 1,
        }
        response = StaticDNSListResponse(**data)
        assert len(response.entries) == 1
        assert response.entries[0].id == "dns1"


class TestStaticDNSDevicesResponse:
    """Tests for StaticDNSDevicesResponse model."""

    def test_empty_response(self):
        response = StaticDNSDevicesResponse()
        assert response.devices == []

    def test_with_devices(self):
        device = StaticDNSDevice(
            mac="aa:bb:cc:dd:ee:ff",
            hostname="workstation",
            ipAddress="192.168.1.50",
        )
        response = StaticDNSDevicesResponse(devices=[device])
        assert len(response.devices) == 1
        assert response.devices[0].mac == "aa:bb:cc:dd:ee:ff"

    def test_from_dict(self):
        data = {
            "devices": [{"mac": "11:22:33:44:55:66", "hostname": "laptop", "ipAddress": "10.0.0.5"}]
        }
        response = StaticDNSDevicesResponse(**data)
        assert len(response.devices) == 1
        assert response.devices[0].hostname == "laptop"
