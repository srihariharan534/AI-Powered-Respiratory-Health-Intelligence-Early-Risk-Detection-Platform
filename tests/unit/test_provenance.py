"""
Validation tests for provenance registries (sources.yaml, licenses.yaml, transformations.yaml).
"""

from pathlib import Path

import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
PROVENANCE_DIR = ROOT_DIR / "data" / "provenance"


def test_sources_registry():
    """Verify sources.yaml contains valid records with required keys."""
    sources_file = PROVENANCE_DIR / "sources.yaml"
    assert sources_file.is_file(), "sources.yaml missing"

    with open(sources_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "sources" in data
    sources = data["sources"]
    assert len(sources) >= 4

    for s in sources:
        assert "id" in s
        assert "name" in s
        assert "type" in s
        assert "status" in s


def test_licenses_registry():
    """Verify licenses.yaml references valid source records and specifies attribution."""
    licenses_file = PROVENANCE_DIR / "licenses.yaml"
    assert licenses_file.is_file(), "licenses.yaml missing"

    with open(licenses_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "licenses" in data
    licenses = data["licenses"]
    assert len(licenses) >= 4

    for lic in licenses:
        assert "source_id" in lic
        assert "license" in lic
        assert "attribution_required" in lic
        assert "status" in lic


def test_transformations_registry():
    """Verify transformations.yaml defines valid pipeline transformations."""
    trans_file = PROVENANCE_DIR / "transformations.yaml"
    assert trans_file.is_file(), "transformations.yaml missing"

    with open(trans_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "transformations" in data
    transformations = data["transformations"]
    assert len(transformations) >= 3

    for t in transformations:
        assert "id" in t
        assert "source" in t
        assert "input_format" in t
        assert "output_format" in t
        assert "status" in t
