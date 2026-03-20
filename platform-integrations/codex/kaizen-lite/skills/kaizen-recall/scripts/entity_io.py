"""Shared entity I/O utilities for Kaizen Codex skills.

Handles reading and writing entities as flat markdown files with YAML
frontmatter, organized in type-nested directories.
"""

from __future__ import annotations

import datetime
import getpass
import os
import re
import tempfile
from pathlib import Path


def _get_log_dir() -> str:
    """Get a user-scoped log directory with restrictive permissions."""
    try:
        uid = os.getuid()
    except AttributeError:
        uid = getpass.getuser()
    log_dir = os.path.join(tempfile.gettempdir(), f"kaizen-{uid}")
    os.makedirs(log_dir, mode=0o700, exist_ok=True)
    return log_dir


_LOG_FILE = os.path.join(_get_log_dir(), "kaizen-codex.log")


def log(component: str, message: str) -> None:
    """Append a timestamped message to the shared log file."""
    if not os.environ.get("KAIZEN_DEBUG"):
        return
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(_LOG_FILE, "a", encoding="utf-8") as handle:
            handle.write(f"[{timestamp}] [{component}] {message}\n")
    except OSError:
        pass


def find_entities_dir() -> Path | None:
    """Locate the entities directory."""
    env_dir = os.environ.get("KAIZEN_ENTITIES_DIR")
    if env_dir:
        path = Path(env_dir)
        return path if path.is_dir() else None

    project_root = os.environ.get("CLAUDE_PROJECT_ROOT")
    candidates: list[Path] = []
    if project_root:
        candidates.append(Path(project_root) / ".kaizen" / "entities")
    candidates.append(Path(".kaizen") / "entities")

    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def get_default_entities_dir() -> Path:
    """Return and create the default entities directory."""
    project_root = os.environ.get("CLAUDE_PROJECT_ROOT", "")
    if project_root:
        base = Path(project_root) / ".kaizen" / "entities"
    else:
        base = Path(".kaizen") / "entities"
    base.mkdir(parents=True, exist_ok=True)
    return base.resolve()


def slugify(text: str, max_length: int = 60) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    if len(text) > max_length:
        text = text[:max_length].rsplit("-", 1)[0]
    return text or "entity"


def unique_filename(directory: Path | str, slug: str) -> Path:
    """Return a Path that does not collide with existing files."""
    directory = Path(directory)
    candidate = directory / f"{slug}.md"
    if not candidate.exists():
        return candidate

    counter = 2
    while True:
        candidate = directory / f"{slug}-{counter}.md"
        if not candidate.exists():
            return candidate
        counter += 1


_FRONTMATTER_KEYS = ("type", "trigger")


def entity_to_markdown(entity: dict[str, str]) -> str:
    """Serialize an entity dict to markdown with YAML frontmatter."""
    lines = ["---"]
    for key in _FRONTMATTER_KEYS:
        value = entity.get(key)
        if value:
            lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")

    content = entity.get("content", "")
    lines.append(content)

    rationale = entity.get("rationale")
    if rationale:
        lines.append("")
        lines.append("## Rationale")
        lines.append("")
        lines.append(rationale)

    lines.append("")
    return "\n".join(lines)


def markdown_to_entity(path: Path | str) -> dict[str, str]:
    """Parse a markdown entity file into a dict."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    entity: dict[str, str] = {}

    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            body = parts[2]
            for line in frontmatter.splitlines():
                line = line.strip()
                if not line:
                    continue
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                if key and value:
                    entity[key] = value
        else:
            body = text
    else:
        body = text

    body = body.strip()
    match = re.search(r"^## Rationale", body, re.MULTILINE)
    if match:
        content = body[: match.start()].strip()
        rationale = body[match.end() :].strip()
        if rationale:
            entity["rationale"] = rationale
    else:
        content = body

    if content:
        entity["content"] = content

    return entity


def load_all_entities(entities_dir: Path | str) -> list[dict[str, str]]:
    """Load every markdown entity under the entities directory."""
    entities_dir = Path(entities_dir)
    entities: list[dict[str, str]] = []
    for markdown_file in sorted(entities_dir.glob("**/*.md")):
        try:
            entity = markdown_to_entity(markdown_file)
            if entity.get("content"):
                entities.append(entity)
        except OSError:
            pass
    return entities


def write_entity_file(directory: Path | str, entity: dict[str, str]) -> Path:
    """Write a single entity as a markdown file under directory."""
    entity_type = entity.get("type", "general")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", entity_type):
        entity_type = "general"

    target_dir = Path(directory) / entity_type
    target_dir.mkdir(parents=True, exist_ok=True)

    slug = slugify(entity.get("content", "entity"))
    final_path = unique_filename(target_dir, slug)
    temp_path = final_path.with_suffix(".tmp")
    temp_path.write_text(entity_to_markdown(entity), encoding="utf-8")
    os.replace(temp_path, final_path)
    return final_path
