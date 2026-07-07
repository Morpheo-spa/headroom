"""Package version metadata."""

from __future__ import annotations

import importlib
import os
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

UNKNOWN_VERSION = "unknown"
VERSION_ENV_VARS = ("HEADROOM_VERSION", "HEADROOM_BUILD_VERSION")


def _clean_version(value: object) -> str | None:
    """Return a non-empty version string, if one is present."""
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _env_version() -> str | None:
    """Return an explicit runtime/build version override."""
    for name in VERSION_ENV_VARS:
        value = _clean_version(os.environ.get(name))
        if value:
            return value
    return None


def _packaged_build_version() -> str | None:
    """Return Docker/image build metadata baked into the installed package."""
    try:
        build_info = importlib.import_module("headroom._build_info")
    except ModuleNotFoundError:
        return None
    return _clean_version(getattr(build_info, "BUILD_VERSION", None))


def _source_root() -> Path | None:
    """Return the repository root when imported from a git checkout."""
    root = Path(__file__).resolve().parents[1]
    if (root / ".git").exists() and (root / "pyproject.toml").exists():
        return root
    return None


def _source_tree_version(root: Path) -> str | None:
    """Compute the version release automation would assign to this checkout."""
    try:
        from headroom.release_version import (
            compute_release_version,
            determine_bump_level,
            get_canonical_version,
            list_release_commits,
            list_release_tags,
        )

        tags = list_release_tags(root)
        previous_tag = compute_release_version(
            canonical_version=get_canonical_version(root),
            level="patch",
            tags=tags,
        ).previous_tag
        commits = list_release_commits(root, previous_tag)
        level = determine_bump_level(commits)
        return compute_release_version(
            canonical_version=get_canonical_version(root),
            level=level,
            tags=tags,
        ).version
    except Exception:
        return None


def get_version() -> str:
    """Return Headroom's runtime version."""
    env_version = _env_version()
    if env_version:
        return env_version

    root = _source_root()
    if root is not None:
        source_version = _source_tree_version(root)
        if source_version:
            return source_version

    build_version = _packaged_build_version()
    if build_version:
        return build_version

    try:
        return version("headroom-ai")
    except PackageNotFoundError:
        return UNKNOWN_VERSION


__version__ = get_version()
