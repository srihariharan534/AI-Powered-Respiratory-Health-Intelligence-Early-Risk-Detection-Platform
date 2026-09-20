"""
NEXUS OpenStreetMap Places Processing Package.
Provides foundation for emergency facilities and administrative points of interest.
"""

from pydantic import BaseModel, ConfigDict, Field


class OSMPlace(BaseModel):
    """Normalized emergency place or facility marker."""
    model_config = ConfigDict(extra="ignore")
    place_id: str
    name: str
    place_type: str  # hospital, clinic, shelter, fire_station, police
    longitude: float = Field(..., ge=-180.0, le=180.0)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    tags: dict[str, str] = Field(default_factory=dict)


def parse_emergency_places(payload: dict) -> list[OSMPlace]:
    """Extract emergency facilities from OSM node/way elements."""
    places = []
    for elem in payload.get("elements", []):
        tags = elem.get("tags", {})
        amenity = tags.get("amenity")
        emergency = tags.get("emergency")

        if amenity in ("hospital", "clinic", "shelter", "police", "fire_station") or emergency:
            lon = elem.get("lon")
            lat = elem.get("lat")
            if lon is not None and lat is not None:
                place_type = amenity or emergency or "facility"
                places.append(
                    OSMPlace(
                        place_id=f"PLACE-{elem['id']}",
                        name=tags.get("name", f"Facility {elem['id']}"),
                        place_type=place_type,
                        longitude=float(lon),
                        latitude=float(lat),
                        tags=tags,
                    )
                )
    return places
