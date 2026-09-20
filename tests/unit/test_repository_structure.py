"""
Structural validation test for NEXUS monorepo architecture.
Verifies essential top-level directories and explicit Python package markers.
"""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_root_directories_exist():
    """Verify all top-level architectural directories exist."""
    required_directories = [
        "apps",
        "services",
        "digital_twin",
        "ml",
        "geospatial",
        "backtesting",
        "data",
        "evaluation",
        "tests",
        "scripts",
        "docs",
        "demo",
        "security",
        "infrastructure",
    ]

    for dir_name in required_directories:
        target_dir = ROOT_DIR / dir_name
        assert target_dir.is_dir(), f"Expected directory '{dir_name}' to exist at {target_dir}"


def test_python_packages_exist():
    """Verify explicit Python package markers exist for foundational services."""
    required_packages = [
        "digital_twin/__init__.py",
        "ml/__init__.py",
        "geospatial/__init__.py",
        "backtesting/__init__.py",
        "services/api/app/__init__.py",
        "services/sync/__init__.py",
        "services/sms/__init__.py",
        "services/simulation/__init__.py",
        "services/recommendations/__init__.py",
    ]

    for pkg_marker in required_packages:
        marker_path = ROOT_DIR / pkg_marker
        assert marker_path.is_file(), f"Expected package marker '{pkg_marker}' at {marker_path}"


def test_frontend_workspace_packages_exist():
    """Verify frontend applications have valid package.json files for workspace management."""
    required_frontend_apps = [
        "apps/command-center/package.json",
        "apps/field-app/package.json",
    ]

    for app_pkg in required_frontend_apps:
        app_pkg_path = ROOT_DIR / app_pkg
        assert app_pkg_path.is_file(), f"Expected frontend package.json at {app_pkg_path}"
