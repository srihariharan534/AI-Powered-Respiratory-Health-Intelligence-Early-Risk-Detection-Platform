"""
Integration tests for PostGIS spatial extension enablement and geometry expressions.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from services.api.app.config import get_settings
from services.api.app.database import close_engine, get_engine


def test_postgis_extension_version():
    """Verify PostGIS is installed and returns a valid version string."""
    settings = get_settings()
    engine = get_engine(settings.DATABASE_URL)

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT PostGIS_Version();"))
            version_str = result.scalar()
            assert version_str is not None, "PostGIS_Version() returned None"
            assert len(version_str) > 0, "PostGIS_Version() returned empty string"
    except OperationalError as exc:
        pytest.skip(
            f"PostgreSQL/PostGIS is not running or unreachable at {settings.DATABASE_URL}: {exc}"
        )
    finally:
        close_engine()


def test_spatial_srid_expression():
    """Verify spatial geometry constructors and ST_SRID functionality."""
    settings = get_settings()
    engine = get_engine(settings.DATABASE_URL)

    try:
        with engine.connect() as conn:
            query = text("SELECT ST_SRID(ST_GeomFromText('POINT(80.2707 13.0827)', 4326));")
            result = conn.execute(query)
            srid = result.scalar()
            assert srid == 4326, f"Expected SRID 4326, got {srid}"
    except OperationalError as exc:
        pytest.skip(
            f"PostgreSQL/PostGIS is not running or unreachable at {settings.DATABASE_URL}: {exc}"
        )
    finally:
        close_engine()


def test_postgis_spatial_operators():
    """Verify PostGIS ST_Intersects, ST_DWithin, ST_Distance, and ST_Transform operators."""
    settings = get_settings()
    engine = get_engine(settings.DATABASE_URL)

    try:
        with engine.connect() as conn:
            # 1. ST_Intersects
            intersects_query = text(
                """
                SELECT ST_Intersects(
                    ST_GeomFromText('POLYGON((80.25 13.07, 80.28 13.07, 80.28 13.09, 80.25 13.09, 80.25 13.07))', 4326),
                    ST_GeomFromText('POINT(80.2707 13.0827)', 4326)
                );
                """
            )
            assert conn.execute(intersects_query).scalar() is True

            # 2. ST_DWithin (geography in meters)
            dwithin_query = text(
                """
                SELECT ST_DWithin(
                    ST_SetSRID(ST_MakePoint(80.2707, 13.0827), 4326)::geography,
                    ST_SetSRID(ST_MakePoint(80.2610, 13.0732), 4326)::geography,
                    2000
                );
                """
            )
            assert conn.execute(dwithin_query).scalar() is True

            # 3. ST_Distance (geography in meters)
            dist_query = text(
                """
                SELECT ST_Distance(
                    ST_SetSRID(ST_MakePoint(80.2707, 13.0827), 4326)::geography,
                    ST_SetSRID(ST_MakePoint(80.2610, 13.0732), 4326)::geography
                );
                """
            )
            dist_meters = conn.execute(dist_query).scalar()
            assert 1400 < dist_meters < 1600

            # 4. ST_Transform to UTM Zone 44N (EPSG:32644)
            transform_query = text(
                """
                SELECT ST_SRID(ST_Transform(
                    ST_SetSRID(ST_MakePoint(80.2707, 13.0827), 4326),
                    32644
                ));
                """
            )
            assert conn.execute(transform_query).scalar() == 32644
    except OperationalError as exc:
        pytest.skip(
            f"PostgreSQL/PostGIS is not running or unreachable at {settings.DATABASE_URL}: {exc}"
        )
    finally:
        close_engine()
