/**
 * Contextual Selection Detail Panel for NEXUS Command Center
 * Displays rich attributes for the clicked map feature (Flood, Road, Bridge, Incident, Facility, Route).
 */

import React from 'react';
import { GisSelectedEntity } from '../../types';
import { SeverityBadge, DataModeBadge } from '../ui';

interface DetailPanelProps {
  selectedEntity: GisSelectedEntity;
  onClose: () => void;
}

export const DetailPanel: React.FC<DetailPanelProps> = ({ selectedEntity, onClose }) => {
  if (!selectedEntity) {
    return (
      <div
        style={{
          padding: '1.25rem',
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '8px',
          color: 'var(--text-muted)',
          fontSize: '0.8rem',
          textAlign: 'center',
        }}
      >
        Click any feature on the operational map (flood polygon, road segment, bridge, incident, hospital, or route) to inspect authoritative telemetry.
      </div>
    );
  }

  return (
    <div
      className="detail-panel"
      role="complementary"
      aria-label="Selected Feature Details"
      style={{
        padding: '1.25rem',
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-strong)',
        borderRadius: '8px',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.8rem',
        fontSize: '0.8rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '0.5rem',
        }}
      >
        <div>
          <span
            style={{
              fontSize: '0.65rem',
              fontWeight: 700,
              letterSpacing: '0.05em',
              textTransform: 'uppercase',
              color: 'var(--text-muted)',
            }}
          >
            {selectedEntity.type} INSPECTION
          </span>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {(selectedEntity.data as any).name || (selectedEntity.data as any).id}
          </h3>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close details"
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            fontSize: '1rem',
            padding: '0.2rem',
          }}
        >
          ✕
        </button>
      </div>

      {/* Dynamic Content based on Entity Type */}
      {selectedEntity.type === 'FLOOD' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Severity:</span>
            <SeverityBadge level={selectedEntity.data.severity} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Water Depth:</span>
            <span style={{ fontWeight: 600 }}>{selectedEntity.data.waterDepthM} meters</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Data Mode:</span>
            <DataModeBadge mode={selectedEntity.data.mode} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Scenario Origin:</span>
            <span style={{ fontFamily: 'var(--font-mono)' }}>{selectedEntity.data.scenarioId}</span>
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginTop: '0.4rem' }}>
            Source: {selectedEntity.data.source}
          </div>
        </div>
      )}

      {selectedEntity.type === 'ROAD' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Status:</span>
            <span
              style={{
                fontWeight: 700,
                color: selectedEntity.data.status === 'BLOCKED' ? 'var(--color-critical)' : 'var(--color-online)',
              }}
            >
              {selectedEntity.data.status}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Accessibility:</span>
            <span>{selectedEntity.data.accessibility}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Speed Limit:</span>
            <span>{selectedEntity.data.speedLimitKmh} km/h</span>
          </div>
          {selectedEntity.data.floodDepthCm !== undefined && (
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Water Depth:</span>
              <span style={{ color: 'var(--color-severe)', fontWeight: 600 }}>
                {selectedEntity.data.floodDepthCm} cm
              </span>
            </div>
          )}
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginTop: '0.4rem' }}>
            Source: {selectedEntity.data.source}
          </div>
        </div>
      )}

      {selectedEntity.type === 'BRIDGE' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Status:</span>
            <span
              style={{
                fontWeight: 700,
                color: selectedEntity.data.status === 'FAILED' ? 'var(--color-critical)' : 'var(--color-online)',
              }}
            >
              {selectedEntity.data.status}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Clearance:</span>
            <span>{selectedEntity.data.clearanceM} m</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Associated Road:</span>
            <span style={{ fontFamily: 'var(--font-mono)' }}>{selectedEntity.data.roadId}</span>
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginTop: '0.4rem' }}>
            Source: {selectedEntity.data.source}
          </div>
        </div>
      )}

      {selectedEntity.type === 'INCIDENT' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Severity:</span>
            <SeverityBadge level={selectedEntity.data.severity} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Event Type:</span>
            <span style={{ fontWeight: 600 }}>{selectedEntity.data.type}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Status:</span>
            <span>{selectedEntity.data.status}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Assigned Unit:</span>
            <span style={{ fontWeight: 600, color: '#60a5fa' }}>
              {selectedEntity.data.assignedUnit || 'Unassigned'}
            </span>
          </div>
          <p style={{ marginTop: '0.3rem', color: 'var(--text-primary)', lineHeight: 1.4 }}>
            {selectedEntity.data.description}
          </p>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>
            Reported at: {selectedEntity.data.reportedAt} • {selectedEntity.data.source}
          </div>
        </div>
      )}

      {(selectedEntity.type === 'HOSPITAL' || selectedEntity.type === 'SHELTER') && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Facility Type:</span>
            <span style={{ fontWeight: 600 }}>{selectedEntity.data.type}</span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Operational Status:</span>
            <span
              style={{
                fontWeight: 700,
                color:
                  selectedEntity.data.operationalStatus === 'OPERATIONAL' || selectedEntity.data.operationalStatus === 'OPEN'
                    ? 'var(--color-online)'
                    : selectedEntity.data.operationalStatus === 'OVERLOADED' || selectedEntity.data.operationalStatus === 'AT_CAPACITY'
                    ? 'var(--color-severe)'
                    : 'var(--color-critical)',
              }}
            >
              {selectedEntity.data.operationalStatus}
            </span>
          </div>

          {selectedEntity.data.floodExposure && (
            <div
              style={{
                padding: '0.4rem 0.6rem',
                borderRadius: '4px',
                backgroundColor: selectedEntity.data.floodExposure.is_exposed ? 'rgba(59, 130, 246, 0.15)' : 'rgba(16, 185, 129, 0.1)',
                border: `1px solid ${selectedEntity.data.floodExposure.is_exposed ? '#3b82f6' : '#10b981'}`,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: '0.72rem',
              }}
            >
              <span style={{ fontWeight: 600, color: selectedEntity.data.floodExposure.is_exposed ? '#60a5fa' : '#34d399' }}>
                {selectedEntity.data.floodExposure.is_exposed ? '⚠️ FLOOD EXPOSURE: YES' : '✓ FLOOD EXPOSURE: CLEAR'}
              </span>
              <span style={{ color: 'var(--text-muted)' }}>
                {selectedEntity.data.floodExposure.scenario_id || 'BASELINE'} ({selectedEntity.data.floodExposure.mode || 'REAL'})
              </span>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Total Capacity:</span>
            <span style={{ fontWeight: 600 }}>{selectedEntity.data.capacityTotal}</span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Available Capacity:</span>
            <span style={{ color: 'var(--color-online)', fontWeight: 700 }}>
              {selectedEntity.data.capacityTotal - selectedEntity.data.capacityOccupied}
            </span>
          </div>

          {selectedEntity.type === 'HOSPITAL' && (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Emergency Care:</span>
                <span style={{ fontWeight: 600, color: selectedEntity.data.emergencyAvailable ? 'var(--color-online)' : 'var(--color-critical)' }}>
                  {selectedEntity.data.emergencyAvailable ? 'AVAILABLE' : 'UNAVAILABLE'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Available ICU Beds:</span>
                <span style={{ fontWeight: 600 }}>{selectedEntity.data.icuAvailable ?? 0}</span>
              </div>
            </>
          )}

          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Accessibility:</span>
            <span>{selectedEntity.data.accessibility || 'ALL_VEHICLES'}</span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Power Backup:</span>
            <span>{selectedEntity.data.powerStatus}</span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.72rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.4rem' }}>
            <span>Source: {selectedEntity.data.source || 'SYSTEM'}</span>
            <span>v{selectedEntity.data.stateVersion || 1} • {selectedEntity.data.lastUpdated}</span>
          </div>
        </div>
      )}


      {selectedEntity.type === 'ROUTE' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Status:</span>
            <span
              style={{
                fontWeight: 700,
                color: selectedEntity.data.status === 'BLOCKED' ? 'var(--color-critical)' : '#60a5fa',
              }}
            >
              {selectedEntity.data.status}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Distance:</span>
            <span style={{ fontWeight: 600 }}>{selectedEntity.data.distanceKm} km</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Est. Travel Time:</span>
            <span style={{ fontWeight: 600 }}>{selectedEntity.data.travelTimeMin} min</span>
          </div>
          {selectedEntity.data.deltaDistanceKm !== undefined && (
            <div
              style={{
                padding: '0.5rem',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                border: '1px solid rgba(59, 130, 246, 0.3)',
                borderRadius: '4px',
                fontSize: '0.75rem',
              }}
            >
              <div style={{ fontWeight: 600, color: '#93c5fd' }}>Dynamic Rerouting Delta:</div>
              <div>Distance: +{selectedEntity.data.deltaDistanceKm} km</div>
              <div>Travel Time: +{selectedEntity.data.deltaTravelTimeMin} min</div>
              <div style={{ marginTop: '0.2rem', color: 'var(--text-muted)' }}>
                {selectedEntity.data.changeExplanation}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
