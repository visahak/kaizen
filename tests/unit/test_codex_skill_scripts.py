from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CODEX_ROOT = REPO_ROOT / "platform-integrations" / "codex" / "kaizen-lite"
INSTALL_SCRIPT = CODEX_ROOT / "install.sh"
RECALL_SCRIPT = CODEX_ROOT / "skills" / "kaizen-recall" / "scripts" / "retrieve_entities.py"
LEARN_SCRIPT = CODEX_ROOT / "skills" / "kaizen-learn" / "scripts" / "save_entities.py"


def run_python_script(
    script: Path,
    cwd: Path,
    *args: str,
    stdin: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd,
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
    )


def write_entity_markdown(path: Path, content: str, trigger: str, rationale: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                "type: guideline",
                f"trigger: {trigger}",
                "---",
                "",
                content,
                "",
                "## Rationale",
                "",
                rationale,
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_codex_save_entities_creates_markdown_files(tmp_path: Path) -> None:
    payload = (
        '{"entities": [{"content": "Use uv run pytest -v for focused test runs", '
        '"rationale": "Verbose output helps when failures happen", '
        '"type": "guideline", '
        '"trigger": "When running individual tests in this repo"}]}'
    )

    result = run_python_script(LEARN_SCRIPT, tmp_path, stdin=payload)

    assert result.returncode == 0
    assert "Added 1 new entity(ies). Total: 1" in result.stdout

    entity_files = list((tmp_path / ".kaizen" / "entities" / "guideline").glob("*.md"))
    assert len(entity_files) == 1
    text = entity_files[0].read_text(encoding="utf-8")
    assert "Use uv run pytest -v for focused test runs" in text
    assert "When running individual tests in this repo" in text


def test_codex_save_entities_deduplicates_existing_content(tmp_path: Path) -> None:
    payload = (
        '{"entities": [{"content": "Prefer python3 over python on macOS", '
        '"rationale": "python is often missing while python3 exists", '
        '"type": "guideline", '
        '"trigger": "When running helper scripts on macOS"}]}'
    )

    first_result = run_python_script(LEARN_SCRIPT, tmp_path, stdin=payload)
    second_result = run_python_script(LEARN_SCRIPT, tmp_path, stdin=payload)

    assert first_result.returncode == 0
    assert second_result.returncode == 0
    assert "Added 0 new entity(ies). Total: 1" in second_result.stdout

    entity_files = list((tmp_path / ".kaizen" / "entities" / "guideline").glob("*.md"))
    assert len(entity_files) == 1


def test_codex_retrieve_entities_orders_relevant_guidance_first(tmp_path: Path) -> None:
    entities_dir = tmp_path / ".kaizen" / "entities" / "guideline"
    write_entity_markdown(
        entities_dir / "image-metadata.md",
        "Use Python PIL for image metadata extraction in sandboxed environments",
        "When extracting image metadata inside a sandbox",
        "System tools may be unavailable",
    )
    write_entity_markdown(
        entities_dir / "pytest.md",
        "Use uv run pytest -v for targeted test debugging",
        "When running focused tests in this repository",
        "Verbose output makes failures easier to inspect",
    )

    result = run_python_script(
        RECALL_SCRIPT,
        tmp_path,
        "--type",
        "guideline",
        "--task",
        "extract image metadata in a sandboxed environment",
    )

    assert result.returncode == 0
    assert "KAIZEN GUIDELINES (2 found)" in result.stdout

    pil_index = result.stdout.index("Use Python PIL for image metadata extraction in sandboxed environments")
    pytest_index = result.stdout.index("Use uv run pytest -v for targeted test debugging")
    assert pil_index < pytest_index


def test_codex_retrieve_entities_handles_missing_entities_dir(tmp_path: Path) -> None:
    result = run_python_script(
        RECALL_SCRIPT,
        tmp_path,
        "--type",
        "guideline",
        "--task",
        "inspect the repository",
    )

    assert result.returncode == 0
    assert "No Kaizen entities exist yet" in result.stdout


def test_codex_install_script_merges_agents_and_preserves_existing_skills(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text(
        "# Existing Instructions\n\nKeep the current repo guidance.\n",
        encoding="utf-8",
    )

    existing_skill = repo_root / ".agents" / "skills" / "existing-skill"
    existing_skill.mkdir(parents=True)
    (existing_skill / "SKILL.md").write_text(
        "---\nname: existing-skill\ndescription: Existing skill.\n---\n",
        encoding="utf-8",
    )

    first_result = subprocess.run(
        ["bash", str(INSTALL_SCRIPT), str(repo_root)],
        text=True,
        capture_output=True,
        check=False,
    )
    second_result = subprocess.run(
        ["bash", str(INSTALL_SCRIPT), str(repo_root)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert first_result.returncode == 0
    assert second_result.returncode == 0

    agents_text = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    assert "# Existing Instructions" in agents_text
    assert agents_text.count("<!-- BEGIN KAIZEN CODEX -->") == 1
    assert agents_text.count("<!-- END KAIZEN CODEX -->") == 1

    assert (repo_root / ".agents" / "skills" / "existing-skill" / "SKILL.md").exists()
    assert (repo_root / ".agents" / "skills" / "kaizen-workflow" / "SKILL.md").exists()
    assert (repo_root / ".agents" / "skills" / "kaizen-recall" / "scripts" / "retrieve_entities.py").exists()
    assert (repo_root / ".agents" / "skills" / "kaizen-learn" / "scripts" / "save_entities.py").exists()
