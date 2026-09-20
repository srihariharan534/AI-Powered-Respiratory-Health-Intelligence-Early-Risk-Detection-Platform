#!/usr/bin/env python3
"""
NEXUS OpenStreetMap Live Acquisition Script.
Extracts road network and infrastructure bounding boxes from OpenStreetMap Overpass API.
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
RAW_OSM_DIR = ROOT_DIR / "data" / "raw" / "osm"

DEFAULT_OVERPASS_ENDPOINT = "https://overpass-api.de/api/interpreter"


def build_overpass_query(bbox: tuple[float, float, float, float]) -> str:
    """
    Construct Overpass QL query for highways and bridges inside bounding box.
    bbox: (min_lat, min_lon, max_lat, max_lon)
    """
    min_lat, min_lon, max_lat, max_lon = bbox
    bbox_str = f"{min_lat},{min_lon},{max_lat},{max_lon}"
    return f"""
    [out:json][timeout:30];
    (
      way["highway"]({bbox_str});
      node(w);
    );
    out body;
    """


def fetch_osm_data(
    bbox: tuple[float, float, float, float],
    output_path: Path | None = None,
    endpoint: str = DEFAULT_OVERPASS_ENDPOINT,
) -> dict:
    """
    Fetch raw OSM payload from Overpass API.
    """
    query = build_overpass_query(bbox)
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")

    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={"User-Agent": "NEXUS-Emergency-Decision-Platform/0.1.0"},
    )

    try:
        print(f"Connecting to Overpass endpoint: {endpoint}")
        with urllib.request.urlopen(req, timeout=45) as response:
            if response.status != 200:
                raise RuntimeError(f"Overpass API returned HTTP {response.status}")
            raw_bytes = response.read()
            payload = json.loads(raw_bytes.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch OSM data: {exc}") from exc

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"Saved raw OSM artifact to: {output_path}")

    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="NEXUS OpenStreetMap Highway Network Extraction Tool"
    )
    parser.add_argument(
        "--bbox",
        type=str,
        help="Bounding box 'min_lat,min_lon,max_lat,max_lon'. Example: '13.05,80.20,13.12,80.30'",
    )
    parser.add_argument(
        "--place",
        type=str,
        help="Named district or operational area tag for artifact filename labeling",
        default="district-demo",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Destination JSON filepath for raw OSM artifact",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print query and parameter configuration without executing network request",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Read bounding box from CLI or environment variable
    bbox_str = args.bbox or os.getenv("NEXUS_OSM_BBOX")
    if not bbox_str:
        err_msg = "ERROR: Missing bounding box. Specify --bbox or set NEXUS_OSM_BBOX."
        print(err_msg, file=sys.stderr)
        return 1

    try:
        coords = [float(c.strip()) for c in bbox_str.split(",")]
        if len(coords) != 4:
            raise ValueError("BBOX must contain exactly 4 comma-separated coordinates")
        min_lat, min_lon, max_lat, max_lon = coords
        if not (-90.0 <= min_lat <= max_lat <= 90.0):
            raise ValueError("Latitude values must be between -90 and 90 degrees")
        if not (-180.0 <= min_lon <= max_lon <= 180.0):
            raise ValueError("Longitude values must be between -180 and 180 degrees")
        bbox = (min_lat, min_lon, max_lat, max_lon)
    except Exception as e:
        print(f"ERROR: Invalid bounding box format: {e}", file=sys.stderr)
        return 1

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    target_output = (
        Path(args.output)
        if args.output
        else RAW_OSM_DIR / f"osm_{args.place}_{timestamp}.json"
    )

    print("=" * 60)
    print("NEXUS OPENSTREETMAP DATA EXTRACTION")
    print("=" * 60)
    print("SOURCE       : OpenStreetMap (Overpass API)")
    print(f"BOUNDING BOX : [{min_lat}, {min_lon}, {max_lat}, {max_lon}]")
    print(f"PLACE IDENT  : {args.place}")
    print(f"DESTINATION  : {target_output}")
    print(f"TIMESTAMP    : {timestamp}")

    if args.dry_run:
        print("\nMODE: DRY RUN (Network request skipped)")
        query = build_overpass_query(bbox)
        print(f"Generated Overpass Query:\n{query}")
        return 0

    print("MODE: LIVE DOWNLOAD")
    try:
        payload = fetch_osm_data(bbox, output_path=target_output)
        elements_count = len(payload.get("elements", []))
        print(f"SUCCESS: Retrieved {elements_count} OSM elements.")
        return 0
    except Exception as err:
        print(f"ERROR: Network extraction failed: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
