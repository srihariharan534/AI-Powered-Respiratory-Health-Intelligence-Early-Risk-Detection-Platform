import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useI18n } from '../../context/I18nContext';
import { useFieldApp } from '../../context/FieldAppContext';
import { LocationResult, LocationService } from '../../services/location/locationService';
import { TransactionCoordinator } from '../../database/repositories/TransactionCoordinator';
import { DurableIncident } from '../../database/types';
import { SyncQueueService } from '../../services/sync/syncQueueService';
import { CanonicalIncidentReport, IncidentEventType, IncidentSeverity } from '../../types';

export const IncidentReportScreen: React.FC = () => {
  const { t } = useI18n();
  const { connectionStatus } = useFieldApp();
  const navigate = useNavigate();

  const [eventType, setEventType] = useState<IncidentEventType>('FLOOD_INUNDATION');
  const [severity, setSeverity] = useState<IncidentSeverity>('HIGH');
  const [priority] = useState<number>(1);
  const [description, setDescription] = useState<string>('');
  const [location, setLocation] = useState<LocationResult | null>(null);
  const [manualCoords, setManualCoords] = useState<{ lon: string; lat: string }>({ lon: '80.2230', lat: '13.0180' });
  const [isCapturingLocation, setIsCapturingLocation] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [isManualLocation, setIsManualLocation] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedMessage, setSubmittedMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const captureGps = async () => {
    setIsCapturingLocation(true);
    setLocationError(null);
    try {
      const pos = await LocationService.getCurrentPosition();
      setLocation(pos);
      setIsManualLocation(false);
    } catch (err: any) {
      setLocationError(err.message || 'GPS acquisition failed.');
    } finally {
      setIsCapturingLocation(false);
    }
  };

  const applyManualLocation = () => {
    try {
      const lon = parseFloat(manualCoords.lon);
      const lat = parseFloat(manualCoords.lat);
      const pos = LocationService.createManualPosition(lon, lat);
      setLocation(pos);
      setIsManualLocation(true);
      setLocationError(null);
    } catch (err: any) {
      setLocationError(err.message);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;

    setErrorMessage(null);

    if (!description.trim()) {
      setErrorMessage('Validation Error: description is mandatory for emergency triage.');
      return;
    }

    const finalLocation = location || LocationService.createManualPosition(
      parseFloat(manualCoords.lon),
      parseFloat(manualCoords.lat)
    );

    const incidentId = `INC-FLD-${Date.now()}`;

    const canonicalReport: CanonicalIncidentReport = {
      schema_version: '1.0.0',
      incident_id: incidentId,
      event_type: eventType,
      severity: severity,
      status: 'OPEN',
      priority: priority,
      location: {
        type: 'Point',
        coordinates: [finalLocation.longitude, finalLocation.latitude],
      },
      reported_at: new Date().toISOString(),
      reported_by: 'FIELD_OFFICER_01',
      description: description.trim(),
      source: 'field_officer',
    };

    const durableIncident: DurableIncident = {
      ...canonicalReport,
      local_record_id: `LOCAL-${Date.now()}`,
      created_locally_at: new Date().toISOString(),
      updated_locally_at: new Date().toISOString(),
      sync_status: 'PENDING_SYNC',
      sync_attempts: 0,
    };

    setIsSubmitting(true);

    try {
      // Atomic multi-store IndexedDB transaction (Incident + Outbox)
      const coordinator = new TransactionCoordinator();
      await coordinator.saveIncidentWithOutbox({
        incident: durableIncident,
      });

      // Notify sync queue service for reactive subscribers
      SyncQueueService.enqueue('INCIDENT', durableIncident);

      const feedback = connectionStatus === 'OFFLINE'
        ? `✓ SAVED ON DEVICE — PENDING SYNC (Incident ID: ${incidentId})`
        : `✓ SAVED ON DEVICE — QUEUED FOR SYNC (Incident ID: ${incidentId})`;

      setSubmittedMessage(feedback);
      setTimeout(() => {
        navigate('/sync');
      }, 1400);
    } catch (err: any) {
      console.error('Storage failure:', err);
      setErrorMessage(`Storage Error: Could not save report on device (${err.message || 'IndexedDB error'}). Free storage space and try again.`);
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0 }}>
          {t('action_report_incident')}
        </h1>
        <button
          onClick={() => navigate('/')}
          style={{
            padding: '0.2rem 0.6rem',
            minHeight: '32px',
            backgroundColor: 'transparent',
            color: 'var(--text-muted)',
            border: 'none',
            fontSize: '0.8rem',
          }}
        >
          ✕ Cancel
        </button>
      </div>

      {connectionStatus === 'OFFLINE' && (
        <div
          style={{
            padding: '0.6rem 0.8rem',
            backgroundColor: 'rgba(234, 179, 8, 0.15)',
            border: '1px solid rgba(234, 179, 8, 0.3)',
            borderRadius: '6px',
            color: '#eab308',
            fontSize: '0.75rem',
            lineHeight: 1.4,
          }}
        >
          {t('offline_notice')}
        </div>
      )}

      {submittedMessage && (
        <div
          style={{
            padding: '0.75rem',
            backgroundColor: 'rgba(34, 197, 94, 0.2)',
            border: '1px solid #22c55e',
            borderRadius: '6px',
            color: '#22c55e',
            fontSize: '0.85rem',
            fontWeight: 600,
          }}
        >
          {submittedMessage}
        </div>
      )}

      {errorMessage && (
        <div
          style={{
            padding: '0.75rem',
            backgroundColor: 'rgba(239, 68, 68, 0.2)',
            border: '1px solid #ef4444',
            borderRadius: '6px',
            color: '#ef4444',
            fontSize: '0.85rem',
            fontWeight: 600,
          }}
        >
          ⚠ {errorMessage}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {/* Event Type */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
          <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Incident Category:
          </label>
          <select
            value={eventType}
            onChange={(e) => setEventType(e.target.value as IncidentEventType)}
          >
            <option value="FLOOD_INUNDATION">Water Inundation / Overflow</option>
            <option value="ROAD_BLOCKED">Corridor Blocked / Impassable</option>
            <option value="BRIDGE_FAILURE">Bridge Failure / Damaged</option>
            <option value="EMBANKMENT_BREACH">Embankment / Levee Breach</option>
            <option value="MEDICAL_EMERGENCY">Medical Emergency / Trauma</option>
            <option value="TRAPPED_PERSONS">Trapped Civilians</option>
            <option value="SHELTER_NEEDED">Emergency Shelter Required</option>
          </select>
        </div>

        {/* Severity Selector */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
          <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Severity Tier:
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.4rem' }}>
            {(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as IncidentSeverity[]).map((s) => (
              <button
                type="button"
                key={s}
                onClick={() => setSeverity(s)}
                style={{
                  minHeight: '40px',
                  backgroundColor: severity === s ? (s === 'CRITICAL' ? '#ef4444' : s === 'HIGH' ? '#f97316' : '#3b82f6') : 'var(--bg-surface)',
                  color: severity === s ? '#fff' : 'var(--text-secondary)',
                  border: `1px solid ${severity === s ? 'transparent' : 'var(--border-subtle)'}`,
                  fontSize: '0.75rem',
                  fontWeight: 700,
                }}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Location Section */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', backgroundColor: 'var(--bg-surface)', padding: '0.75rem', borderRadius: '8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
              Location Coordinates (WGS84):
            </span>
            {location && (
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  color: location.source === 'GPS' ? '#22c55e' : '#eab308',
                }}
              >
                {location.source === 'GPS' ? '● GPS VERIFIED' : '○ MANUAL COORDS'}
              </span>
            )}
          </div>

          {location ? (
            <div style={{ fontSize: '0.8rem', color: 'var(--text-primary)', fontFamily: 'monospace' }}>
              [{location.longitude.toFixed(6)}, {location.latitude.toFixed(6)}]
              {location.accuracyMeters && <span style={{ color: 'var(--text-muted)', marginLeft: '0.5rem' }}>±{location.accuracyMeters}m</span>}
            </div>
          ) : (
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No location captured yet</div>
          )}

          {locationError && (
            <div style={{ color: '#ef4444', fontSize: '0.75rem' }}>⚠ {locationError}</div>
          )}

          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.3rem' }}>
            <button
              type="button"
              onClick={captureGps}
              disabled={isCapturingLocation}
              style={{
                flex: 1,
                minHeight: '38px',
                backgroundColor: 'var(--bg-card)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)',
                fontSize: '0.75rem',
                fontWeight: 600,
              }}
            >
              {isCapturingLocation ? 'Acquiring...' : '📍 Capture GPS'}
            </button>
            <button
              type="button"
              onClick={() => setIsManualLocation(!isManualLocation)}
              style={{
                minHeight: '38px',
                padding: '0 0.75rem',
                backgroundColor: 'transparent',
                color: 'var(--text-muted)',
                border: '1px solid var(--border-subtle)',
                fontSize: '0.75rem',
              }}
            >
              Manual
            </button>
          </div>

          {isManualLocation && (
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.4rem' }}>
              <input
                type="text"
                placeholder="Lon (80.223)"
                value={manualCoords.lon}
                onChange={(e) => setManualCoords({ ...manualCoords, lon: e.target.value })}
                style={{ flex: 1, padding: '0.4rem', fontSize: '0.8rem' }}
              />
              <input
                type="text"
                placeholder="Lat (13.018)"
                value={manualCoords.lat}
                onChange={(e) => setManualCoords({ ...manualCoords, lat: e.target.value })}
                style={{ flex: 1, padding: '0.4rem', fontSize: '0.8rem' }}
              />
              <button
                type="button"
                onClick={applyManualLocation}
                style={{ minHeight: '36px', padding: '0 0.6rem', fontSize: '0.75rem', backgroundColor: '#3b82f6', color: '#fff', border: 'none' }}
              >
                Set
              </button>
            </div>
          )}
        </div>

        {/* Description */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
          <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            {t('description_label')}:
          </label>
          <textarea
            required
            rows={3}
            placeholder="Report ground depth, stranded count, impassable landmarks..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isSubmitting}
          style={{
            padding: '1rem',
            backgroundColor: isSubmitting ? 'var(--bg-card)' : 'var(--color-danger)',
            color: '#fff',
            border: 'none',
            fontSize: '1rem',
            fontWeight: 800,
            letterSpacing: '0.02em',
            marginTop: '0.5rem',
            cursor: isSubmitting ? 'not-allowed' : 'pointer',
          }}
        >
          {isSubmitting
            ? 'Saving on Device...'
            : connectionStatus === 'OFFLINE'
            ? 'Save on Device'
            : t('btn_submit')}
        </button>
      </form>
    </div>
  );
};
