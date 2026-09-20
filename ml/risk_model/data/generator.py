"""
Reference Dataset Generator for Baseline Flood Risk Model (Phase 17).
Generates a deterministic reference dataset across the Cooum Basin operational zone.
Explicitly designated and documented as: SYNTHETIC_SCENARIO_OBSERVATION.
Never claimed as uncalibrated real-world truth.
"""

from pathlib import Path
import numpy as np
import pandas as pd


def generate_reference_dataset(
    output_path: Path,
    num_samples: int = 500,
    random_seed: int = 42,
) -> pd.DataFrame:
    """
    Generates deterministic synthetic observations of environmental features
    and operational disruption labels over Chennai EOC operational sector.
    """
    rng = np.random.RandomState(random_seed)

    # Core coordinates centered around Chennai Cooum basin [80.25 - 80.29 E, 13.06 - 13.10 N]
    lons = rng.uniform(80.250, 80.285, size=num_samples)
    lats = rng.uniform(13.065, 13.095, size=num_samples)

    # Hydrological & Topographic features
    # Rainfall: Exponential distribution simulating storm events (0 to 180mm)
    rainfall_24h = rng.exponential(scale=35.0, size=num_samples)
    rainfall_1h = rainfall_24h * rng.uniform(0.1, 0.45, size=num_samples)

    # Elevation: Low-lying coastal floodplain (1.5m to 22.0m)
    elevation = rng.uniform(1.5, 20.0, size=num_samples)

    # Distance to river/drainage channel (20m to 3500m)
    dist_river = rng.uniform(20.0, 3500.0, size=num_samples)

    # Slope in degrees (flat terrain, mostly 0.2 to 4.5 degrees)
    slope = rng.uniform(0.1, 5.0, size=num_samples)

    # Road density (0.5 to 15.0 km/km2)
    road_density = rng.uniform(0.5, 14.0, size=num_samples)

    # Critical facility exposure count (0 to 8 facilities nearby)
    infra_count = rng.poisson(lam=1.5, size=num_samples)
    infra_count = np.clip(infra_count, 0, 15)

    # Physical Latent Disruption Model for Target Label Generation:
    # High rainfall + low elevation + proximity to river -> higher log-odds of disruption
    z_score = (
        0.035 * rainfall_24h
        + 0.05 * rainfall_1h
        - 0.28 * elevation
        - 0.0012 * dist_river
        - 0.15 * slope
        + 0.08 * road_density
        + 0.12 * infra_count
        + 0.85  # Adjusted intercept for realistic event positive rate (~32%)
    )

    # Add realistic environmental noise
    noise = rng.normal(0, 0.65, size=num_samples)
    latent_prob = 1.0 / (1.0 + np.exp(-(z_score + noise)))

    # Operational disruption binary label: 1 if inundation >= 15cm / impassable
    target = (latent_prob >= 0.50).astype(int)

    # Create DataFrame
    data = {
        "sample_id": [f"OBS-{i+1:04d}" for i in range(num_samples)],
        "timestamp": [
            f"2026-09-{10 + (i % 8):02d}T{rng.randint(0, 24):02d}:{rng.randint(0, 60):02d}:00Z"
            for i in range(num_samples)
        ],
        "longitude": np.round(lons, 5),
        "latitude": np.round(lats, 5),
        "rainfall_mm_1h": np.round(rainfall_1h, 2),
        "rainfall_mm_24h": np.round(rainfall_24h, 2),
        "elevation_m": np.round(elevation, 2),
        "distance_to_river_m": np.round(dist_river, 1),
        "slope_degrees": np.round(slope, 2),
        "road_density_km": np.round(road_density, 2),
        "infrastructure_exposure_count": infra_count.astype(int),
        "operational_flood_risk": target,
        "dataset_mode": "SYNTHETIC_SCENARIO_OBSERVATION",
    }

    df = pd.DataFrame(data)

    # Ensure parent dir exists and save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df


if __name__ == "__main__":
    target_path = Path(__file__).resolve().parent / "reference_flood_risk_dataset.csv"
    df = generate_reference_dataset(target_path)
    print(f"Generated {len(df)} samples to {target_path}. Positive rate: {df['operational_flood_risk'].mean():.2%}")
