"""Security tests for the UniFi MCP Server."""

import importlib.util


def test_diskcache_not_installed():
    """Verify diskcache (CVE-2025-69872) is not in the dependency tree.

    diskcache was removed when fastmcp upgraded to 3.x. This test ensures
    it doesn't get reintroduced as a transitive dependency.
    """
    assert importlib.util.find_spec("diskcache") is None, (
        "diskcache should not be installed. "
        "It has an unpatched unsafe deserialization vulnerability (CVE-2025-69872)."
    )


def test_no_diskcache_imports_in_codebase():
    """Verify our codebase doesn't import or use diskcache."""
    import os
    import re

    diskcache_imports = []

    for root, dirs, files in os.walk("src"):
        dirs[:] = [d for d in dirs if not d.startswith("__")]

        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, encoding="utf-8") as f:
                    content = f.read()
                    if re.search(r"import\s+diskcache|from\s+diskcache", content):
                        diskcache_imports.append(filepath)

    assert len(diskcache_imports) == 0, (
        f"Found diskcache imports in: {diskcache_imports}. "
        "We should not use diskcache directly due to CVE-2025-69872."
    )
