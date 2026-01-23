"""Unit tests for src/utils/audit.py."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.utils.audit import (
    AuditLogger,
    audit_action,
    get_audit_logger,
    log_audit,
)


class TestAuditLoggerInit:
    """Tests for AuditLogger initialization."""

    def test_init_default_log_file(self, tmp_path):
        """Test AuditLogger with default log file."""
        with patch.object(Path, "parent", tmp_path):
            logger = AuditLogger()
            assert logger.log_file == Path("audit.log")

    def test_init_custom_log_file_str(self, tmp_path):
        """Test AuditLogger with custom string log file path."""
        log_path = tmp_path / "custom_audit.log"
        logger = AuditLogger(log_file=str(log_path))
        assert logger.log_file == log_path

    def test_init_custom_log_file_path(self, tmp_path):
        """Test AuditLogger with custom Path log file."""
        log_path = tmp_path / "custom_audit.log"
        logger = AuditLogger(log_file=log_path)
        assert logger.log_file == log_path

    def test_init_creates_parent_directory(self, tmp_path):
        """Test that AuditLogger creates parent directory if needed."""
        log_path = tmp_path / "nested" / "dir" / "audit.log"
        AuditLogger(log_file=log_path)
        assert log_path.parent.exists()

    def test_init_custom_log_level(self, tmp_path):
        """Test AuditLogger with custom log level."""
        log_path = tmp_path / "audit.log"
        logger = AuditLogger(log_file=log_path, log_level="DEBUG")
        assert logger is not None


class TestAuditLoggerLogOperation:
    """Tests for AuditLogger.log_operation method."""

    def test_log_operation_basic(self, tmp_path):
        """Test basic log_operation functionality."""
        log_path = tmp_path / "audit.log"
        logger = AuditLogger(log_file=log_path)

        logger.log_operation(
            operation="create_network",
            parameters={"name": "TestNet", "vlan_id": 100},
            result="success",
        )

        assert log_path.exists()
        content = log_path.read_text()
        record = json.loads(content.strip())

        assert record["operation"] == "create_network"
        assert record["parameters"]["name"] == "TestNet"
        assert record["result"] == "success"
        assert "timestamp" in record

    def test_log_operation_with_user(self, tmp_path):
        """Test log_operation with user parameter."""
        log_path = tmp_path / "audit.log"
        logger = AuditLogger(log_file=log_path)

        logger.log_operation(
            operation="delete_firewall_rule",
            parameters={"rule_id": "rule-123"},
            result="success",
            user="admin@example.com",
        )

        content = log_path.read_text()
        record = json.loads(content.strip())

        assert record["user"] == "admin@example.com"

    def test_log_operation_with_site_id(self, tmp_path):
        """Test log_operation with site_id parameter."""
        log_path = tmp_path / "audit.log"
        logger = AuditLogger(log_file=log_path)

        logger.log_operation(
            operation="update_wlan",
            parameters={"wlan_id": "wlan-456"},
            result="success",
            site_id="default",
        )

        content = log_path.read_text()
        record = json.loads(content.strip())

        assert record["site_id"] == "default"

    def test_log_operation_dry_run(self, tmp_path):
        """Test log_operation with dry_run flag."""
        log_path = tmp_path / "audit.log"
        logger = AuditLogger(log_file=log_path)

        logger.log_operation(
            operation="create_firewall_zone",
            parameters={"name": "IoT"},
            result="preview",
            dry_run=True,
        )

        content = log_path.read_text()
        record = json.loads(content.strip())

        assert record["dry_run"] is True

    def test_log_operation_failed_result(self, tmp_path):
        """Test log_operation with failed result logs warning."""
        log_path = tmp_path / "audit.log"
        logger = AuditLogger(log_file=log_path)

        with patch.object(logger.logger, "warning") as mock_warning:
            logger.log_operation(
                operation="delete_network",
                parameters={"network_id": "net-999"},
                result="failed",
            )

            mock_warning.assert_called()

    def test_log_operation_success_logs_info(self, tmp_path):
        """Test log_operation with success result logs info."""
        log_path = tmp_path / "audit.log"
        logger = AuditLogger(log_file=log_path)

        with patch.object(logger.logger, "info") as mock_info:
            logger.log_operation(
                operation="restart_device",
                parameters={"device_mac": "aa:bb:cc:dd:ee:ff"},
                result="success",
            )

            mock_info.assert_called()

    def test_log_operation_file_write_error(self, tmp_path):
        """Test log_operation handles file write errors gracefully."""
        log_path = tmp_path / "audit.log"
        logger = AuditLogger(log_file=log_path)

        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with patch.object(logger.logger, "error") as mock_error:
                # Should not raise, but log error
                logger.log_operation(
                    operation="test_op",
                    parameters={},
                    result="success",
                )
                mock_error.assert_called()

    def test_log_operation_multiple_entries(self, tmp_path):
        """Test log_operation appends multiple entries."""
        log_path = tmp_path / "audit.log"
        logger = AuditLogger(log_file=log_path)

        logger.log_operation(
            operation="op1",
            parameters={"key": "value1"},
            result="success",
        )
        logger.log_operation(
            operation="op2",
            parameters={"key": "value2"},
            result="success",
        )

        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 2

        record1 = json.loads(lines[0])
        record2 = json.loads(lines[1])

        assert record1["operation"] == "op1"
        assert record2["operation"] == "op2"


class TestAuditLoggerGetRecentOperations:
    """Tests for AuditLogger.get_recent_operations method."""

    def test_get_recent_operations_empty_file(self, tmp_path):
        """Test get_recent_operations with no log file."""
        log_path = tmp_path / "nonexistent.log"
        logger = AuditLogger(log_file=log_path)

        result = logger.get_recent_operations()

        assert result == []

    def test_get_recent_operations_basic(self, tmp_path):
        """Test get_recent_operations returns entries."""
        log_path = tmp_path / "audit.log"
        logger = AuditLogger(log_file=log_path)

        # Add some entries
        for i in range(5):
            logger.log_operation(
                operation=f"operation_{i}",
                parameters={"index": i},
                result="success",
            )

        result = logger.get_recent_operations()

        assert len(result) == 5
        # Should be in reverse order (most recent first)
        assert result[0]["operation"] == "operation_4"
        assert result[4]["operation"] == "operation_0"

    def test_get_recent_operations_with_limit(self, tmp_path):
        """Test get_recent_operations respects limit."""
        log_path = tmp_path / "audit.log"
        logger = AuditLogger(log_file=log_path)

        for i in range(10):
            logger.log_operation(
                operation=f"operation_{i}",
                parameters={"index": i},
                result="success",
            )

        result = logger.get_recent_operations(limit=3)

        assert len(result) == 3
        # Most recent entries
        assert result[0]["operation"] == "operation_9"

    def test_get_recent_operations_filter_by_operation(self, tmp_path):
        """Test get_recent_operations filters by operation name."""
        log_path = tmp_path / "audit.log"
        logger = AuditLogger(log_file=log_path)

        logger.log_operation(
            operation="create_network",
            parameters={"name": "Net1"},
            result="success",
        )
        logger.log_operation(
            operation="delete_network",
            parameters={"name": "Net2"},
            result="success",
        )
        logger.log_operation(
            operation="create_network",
            parameters={"name": "Net3"},
            result="success",
        )

        result = logger.get_recent_operations(operation="create_network")

        assert len(result) == 2
        assert all(r["operation"] == "create_network" for r in result)

    def test_get_recent_operations_invalid_json(self, tmp_path):
        """Test get_recent_operations handles invalid JSON lines."""
        log_path = tmp_path / "audit.log"
        logger = AuditLogger(log_file=log_path)

        # Write valid entry
        logger.log_operation(
            operation="valid_op",
            parameters={},
            result="success",
        )

        # Append invalid JSON directly
        with open(log_path, "a") as f:
            f.write("this is not valid json\n")

        # Write another valid entry
        logger.log_operation(
            operation="another_valid",
            parameters={},
            result="success",
        )

        with patch.object(logger.logger, "warning") as mock_warning:
            result = logger.get_recent_operations()

            # Should skip invalid JSON and return valid entries
            assert len(result) == 2
            mock_warning.assert_called()

    def test_get_recent_operations_empty_lines(self, tmp_path):
        """Test get_recent_operations handles empty lines."""
        log_path = tmp_path / "audit.log"
        logger = AuditLogger(log_file=log_path)

        logger.log_operation(
            operation="test_op",
            parameters={},
            result="success",
        )

        # Append empty lines
        with open(log_path, "a") as f:
            f.write("\n\n")

        result = logger.get_recent_operations()

        assert len(result) == 1

    def test_get_recent_operations_read_error(self, tmp_path):
        """Test get_recent_operations handles read errors."""
        log_path = tmp_path / "audit.log"
        logger = AuditLogger(log_file=log_path)

        # Create the file
        log_path.touch()

        with patch("builtins.open", side_effect=OSError("Read error")):
            with patch.object(logger.logger, "error") as mock_error:
                result = logger.get_recent_operations()

                assert result == []
                mock_error.assert_called()


class TestGetAuditLogger:
    """Tests for get_audit_logger function."""

    def test_get_audit_logger_returns_instance(self, tmp_path):
        """Test get_audit_logger returns an AuditLogger instance."""
        # Reset global state
        import src.utils.audit as audit_module

        audit_module._audit_logger = None

        log_path = tmp_path / "audit.log"
        logger = get_audit_logger(log_file=log_path)

        assert isinstance(logger, AuditLogger)

    def test_get_audit_logger_singleton(self, tmp_path):
        """Test get_audit_logger returns same instance on subsequent calls."""
        import src.utils.audit as audit_module

        audit_module._audit_logger = None

        log_path = tmp_path / "audit.log"
        logger1 = get_audit_logger(log_file=log_path)
        logger2 = get_audit_logger()

        assert logger1 is logger2


class TestLogAudit:
    """Tests for log_audit convenience function."""

    def test_log_audit_basic(self, tmp_path):
        """Test log_audit convenience function."""
        import src.utils.audit as audit_module

        audit_module._audit_logger = None

        log_path = tmp_path / "audit.log"
        log_audit(
            operation="create_wlan",
            parameters={"name": "GuestWiFi"},
            result="success",
            log_file=log_path,
        )

        assert log_path.exists()
        content = log_path.read_text()
        record = json.loads(content.strip())

        assert record["operation"] == "create_wlan"
        assert record["result"] == "success"

    def test_log_audit_with_all_params(self, tmp_path):
        """Test log_audit with all parameters."""
        import src.utils.audit as audit_module

        audit_module._audit_logger = None

        log_path = tmp_path / "audit.log"
        log_audit(
            operation="delete_client",
            parameters={"mac": "aa:bb:cc:dd:ee:ff"},
            result="success",
            user="admin",
            site_id="site-001",
            dry_run=True,
            log_file=log_path,
        )

        content = log_path.read_text()
        record = json.loads(content.strip())

        assert record["operation"] == "delete_client"
        assert record["site_id"] == "site-001"
        assert record["dry_run"] is True


class TestAuditAction:
    """Tests for audit_action async function."""

    @pytest.mark.asyncio
    async def test_audit_action_basic(self, tmp_path):
        """Test audit_action basic functionality."""
        import src.utils.audit as audit_module

        audit_module._audit_logger = None

        log_path = tmp_path / "audit.log"
        mock_settings = MagicMock()
        mock_settings.audit_log_file = str(log_path)

        await audit_action(
            settings=mock_settings,
            action_type="create_firewall_zone",
            resource_type="firewall_zone",
            resource_id="zone-123",
            site_id="default",
        )

        assert log_path.exists()
        content = log_path.read_text()
        record = json.loads(content.strip())

        assert record["operation"] == "create_firewall_zone"
        assert record["parameters"]["resource_type"] == "firewall_zone"
        assert record["parameters"]["resource_id"] == "zone-123"
        assert record["parameters"]["site_id"] == "default"

    @pytest.mark.asyncio
    async def test_audit_action_with_details(self, tmp_path):
        """Test audit_action with additional details."""
        import src.utils.audit as audit_module

        audit_module._audit_logger = None

        log_path = tmp_path / "audit.log"
        mock_settings = MagicMock()
        mock_settings.audit_log_file = str(log_path)

        await audit_action(
            settings=mock_settings,
            action_type="update_network",
            resource_type="network",
            resource_id="net-456",
            site_id="branch-office",
            details={"old_name": "OldNet", "new_name": "NewNet"},
        )

        content = log_path.read_text()
        record = json.loads(content.strip())

        assert record["parameters"]["details"]["old_name"] == "OldNet"
        assert record["parameters"]["details"]["new_name"] == "NewNet"

    @pytest.mark.asyncio
    async def test_audit_action_no_audit_log_file(self, tmp_path):
        """Test audit_action when settings has no audit_log_file."""
        import src.utils.audit as audit_module

        audit_module._audit_logger = None

        mock_settings = MagicMock(spec=[])  # No audit_log_file attribute

        # Should not raise, uses default log file
        await audit_action(
            settings=mock_settings,
            action_type="test_action",
            resource_type="test",
            resource_id="id-123",
            site_id="default",
        )

    @pytest.mark.asyncio
    async def test_audit_action_none_details(self, tmp_path):
        """Test audit_action with None details."""
        import src.utils.audit as audit_module

        audit_module._audit_logger = None

        log_path = tmp_path / "audit.log"
        mock_settings = MagicMock()
        mock_settings.audit_log_file = str(log_path)

        await audit_action(
            settings=mock_settings,
            action_type="delete_zone",
            resource_type="zone",
            resource_id="zone-789",
            site_id="default",
            details=None,
        )

        content = log_path.read_text()
        record = json.loads(content.strip())

        assert "details" not in record["parameters"]
