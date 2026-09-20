"""
Unit tests for environment and configuration validation (Phase 02).
"""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_core_configuration_files_exist():
    """Verify essential project environment and configuration files exist."""
    required_files = [
        "pyproject.toml",
        "package.json",
        "Makefile",
        ".env.example",
        "docker-compose.yml",
        ".nvmrc",
        ".dockerignore",
    ]
    for filename in required_files:
        path = ROOT_DIR / filename
        assert path.is_file(), f"Configuration file missing: {filename}"


def test_dockerfiles_exist():
    """Verify required service Dockerfiles exist."""
    dockerfiles = [
        "infrastructure/docker/api/Dockerfile",
        "infrastructure/docker/command-center/Dockerfile",
        "infrastructure/docker/field-app/Dockerfile",
    ]
    for df in dockerfiles:
        path = ROOT_DIR / df
        assert path.is_file(), f"Dockerfile missing: {df}"


def test_env_example_has_phase2_variables():
    """Verify .env.example contains fundamental environment variables."""
    env_example = ROOT_DIR / ".env.example"
    content = env_example.read_text(encoding="utf-8")
    assert "APP_ENV" in content
    assert "API_HOST" in content
    assert "API_PORT" in content
    assert "LOG_LEVEL" in content


def test_package_json_workspaces():
    """Verify root package.json defines correct workspaces."""
    import json

    pkg_path = ROOT_DIR / "package.json"
    with open(pkg_path, "r", encoding="utf-8") as f:
        pkg_data = json.load(f)
    assert "workspaces" in pkg_data
    assert "apps/*" in pkg_data["workspaces"]
