#!/usr/bin/env python3
"""
NEXUS Environment Health Check Script.
Validates developer machine toolchains, project files, and environment requirements.
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def check_python_version() -> tuple[bool, str]:
    major, minor = sys.version_info[:2]
    version_str = f"{major}.{minor}.{sys.version_info.micro}"
    if (major, minor) >= (3, 10):
        return True, f"Python {version_str}"
    return False, f"Python {version_str} (Requires >= 3.10)"


def check_node_version() -> tuple[bool, str]:
    node_bin = shutil.which("node")
    if not node_bin:
        return False, "Node.js not found in PATH"
    try:
        res = subprocess.run([node_bin, "--version"], capture_output=True, text=True, check=True)
        return True, f"Node.js {res.stdout.strip()}"
    except Exception as e:
        return False, f"Node.js check failed: {e}"


def check_package_manager() -> tuple[bool, str]:
    npm_bin = shutil.which("npm")
    if not npm_bin:
        return False, "npm not found in PATH"
    try:
        res = subprocess.run([npm_bin, "--version"], capture_output=True, text=True, check=True)
        return True, f"npm {res.stdout.strip()}"
    except Exception as e:
        return False, f"npm check failed: {e}"


def check_docker() -> tuple[bool, str]:
    docker_bin = shutil.which("docker")
    if not docker_bin:
        return False, "Docker not found in PATH"
    try:
        res = subprocess.run([docker_bin, "--version"], capture_output=True, text=True, check=True)
        return True, res.stdout.strip()
    except Exception as e:
        return False, f"Docker check failed: {e}"


def check_required_files() -> tuple[bool, str]:
    required_files = [
        "pyproject.toml",
        "package.json",
        "Makefile",
        ".env.example",
        "docker-compose.yml",
        ".nvmrc",
        ".dockerignore",
    ]
    missing = [f for f in required_files if not (ROOT_DIR / f).is_file()]
    if missing:
        return False, f"Missing required file(s): {', '.join(missing)}"
    return True, f"All {len(required_files)} core configuration files present"


def run_all_checks() -> bool:
    print("=" * 60)
    print(" NEXUS ENVIRONMENT HEALTH CHECK (PHASE 02)")
    print("=" * 60)

    checks = [
        ("Python Version", check_python_version),
        ("Node.js Version", check_node_version),
        ("Package Manager", check_package_manager),
        ("Docker Engine", check_docker),
        ("Configuration Files", check_required_files),
    ]

    all_passed = True
    for label, fn in checks:
        passed, msg = fn()
        icon = "[PASS]" if passed else "[WARN]"
        print(f"{icon} {label:<22} : {msg}")
        if not passed:
            all_passed = False

    print("-" * 60)
    if all_passed:
        print("Status: Environment ready for NEXUS development.")
    else:
        print("Status: Environment has warnings or missing components.")
    print("=" * 60)
    return all_passed


if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)
