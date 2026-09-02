"""Tests for the Hermes memory-provider bundle and its installer."""

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.platform_integrations

_REPO_ROOT = Path(__file__).parent.parent.parent
_HERMES_PLUGIN_ROOT = _REPO_ROOT / "platform-integrations/hermes/plugins/evolve"

# The exact rendered bundle. Pinned so a new shared file under plugin-source/
# cannot silently fan into the Hermes bundle (target_excludes is opt-out).
_EXPECTED_BUNDLE = {
    "README.md",
    "__init__.py",
    "backend.py",
    "guideline_gen.py",
    "lib/evolve-lite/__init__.py",
    "lib/evolve-lite/audit.py",
    "lib/evolve-lite/audit_recall.py",
    "lib/evolve-lite/config.py",
    "lib/evolve-lite/entity_io.py",
    "lib/evolve-lite/retention.py",
    "plugin.yaml",
    "trajectory_adapter.py",
}


def _bundle_files():
    return {
        p.relative_to(_HERMES_PLUGIN_ROOT).as_posix()
        for p in _HERMES_PLUGIN_ROOT.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }


class TestHermesBundleStructure:
    def test_bundle_contains_exactly_the_expected_files(self):
        assert _bundle_files() == _EXPECTED_BUNDLE

    def test_no_evolve_lite_skills_shipped(self):
        # The Hermes provider drives the loop from MemoryProvider callbacks, not
        # from prompt-invoked skills, so the shared skills/ tree must not ship.
        assert not (_HERMES_PLUGIN_ROOT / "skills").exists()

    def test_plugin_yaml_declares_no_pip_dependencies(self):
        data = yaml.safe_load((_HERMES_PLUGIN_ROOT / "plugin.yaml").read_text())
        assert data["name"] == "evolve"
        assert data["pip_dependencies"] == [], (
            "the Hermes bundle must stay install-free — no runtime pip dependency"
        )
