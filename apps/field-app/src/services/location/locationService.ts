/**
 * Location Service Abstraction (Phase 22).
 * Supports device geolocation (WGS84 EPSG:4326) and explicit manual map coordinate fallback.
 * Critical Rule: Never fabricates artificial GPS coordinates.
 */

export interface LocationResult {
  longitude: number;
  latitude: number;
  accuracyMeters?: number;
  timestamp: string;
  source: 'GPS' | 'MANUAL';
}

export class LocationService {
  public static async getCurrentPosition(timeoutMs: number = 8000): Promise<LocationResult> {
    if (!navigator.geolocation) {
      throw new Error('Geolocation is not supported by this device / browser.');
    }

    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        reject(new Error('GPS acquisition timed out. Use manual coordinate selection.'));
      }, timeoutMs);

      navigator.geolocation.getCurrentPosition(
        (pos) => {
          clearTimeout(timeoutId);
          resolve({
            longitude: Number(pos.coords.longitude.toFixed(6)),
            latitude: Number(pos.coords.latitude.toFixed(6)),
            accuracyMeters: Math.round(pos.coords.accuracy),
            timestamp: new Date().toISOString(),
            source: 'GPS',
          });
        },
        (err) => {
          clearTimeout(timeoutId);
          let message = 'Unable to acquire GPS location.';
          if (err.code === err.PERMISSION_DENIED) {
            message = 'GPS permission denied. Please allow location access or set manual coordinates.';
          } else if (err.code === err.POSITION_UNAVAILABLE) {
            message = 'GPS position unavailable. Use manual coordinates.';
          }
          reject(new Error(message));
        },
        {
          enableHighAccuracy: true,
          timeout: timeoutMs,
          maximumAge: 10000,
        }
      );
    });
  }

  public static createManualPosition(longitude: number, latitude: number): LocationResult {
    // Validate bounds
    if (longitude < -180 || longitude > 180 || latitude < -90 || latitude > 90) {
      throw new Error(`Coordinates out of bounds: [${longitude}, ${latitude}]`);
    }

    return {
      longitude: Number(longitude.toFixed(6)),
      latitude: Number(latitude.toFixed(6)),
      timestamp: new Date().toISOString(),
      source: 'MANUAL',
    };
  }
}
