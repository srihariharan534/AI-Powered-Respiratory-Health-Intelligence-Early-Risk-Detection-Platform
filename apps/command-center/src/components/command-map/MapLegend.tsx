/**
 * Reusable Map Legend for NEXUS Live GIS Dashboard
 * Provides clear accessible labels, icons, and severity symbology without relying only on color.
 */

import React from 'react';

interface MapLegendProps {
  visibleLayers: Record<string, boolean>;
}

export const MapLegend: React.FC<MapLegendProps> = ({ visibleLayers }) => {
  return (
    <div
      className="map-legend"
      role="region"
      aria-label="Map Symbology Legend"
      style={{
        backgroundColor: 'rgba(17, 22, 34, 0.92)',
        backdropFilter: 'blur(6px)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '6px',
        padding: '0.75rem',
        fontSize: '0.72rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.4rem',
        boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
      }}
    >
      <div
        style={{
          fontWeight: 700,
          letterSpacing: '0.05em',
          textTransform: 'uppercase',
          color: 'var(--text-muted)',
          marginBottom: '0.2rem',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '0.2rem',
        }}
      >
        Operational Legend
      </div>

      {visibleLayers.flood && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span
            style={{
              width: '12px',
              height: '12px',
              backgroundColor: 'rgba(239, 68, 68, 0.4)',
              border: '1px solid #ef4444',
              borderRadius: '2px',
              display: 'inline-block',
            }}
          />
          <span style={{ color: 'var(--text-primary)' }}>■ Flood Hazard (Critical/Mod)</span>
        </div>
      )}

      {visibleLayers.roads && (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span
              style={{
                width: '14px',
                height: '3px',
                backgroundColor: '#10b981',
                display: 'inline-block',
              }}
            />
            <span style={{ color: 'var(--text-primary)' }}>━ Road (Open)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span
              style={{
                width: '14px',
                height: '3px',
                backgroundColor: '#ef4444',
                display: 'inline-block',
              }}
            />
            <span style={{ color: 'var(--text-primary)' }}>━ Road (Blocked / Flooded)</span>
          </div>
        </>
      )}

      {visibleLayers.routes && (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span
              style={{
                width: '14px',
                height: '4px',
                backgroundColor: '#3b82f6',
                display: 'inline-block',
                borderRadius: '1px',
              }}
            />
            <span style={{ color: 'var(--text-primary)' }}>━ Active Detour Route</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span
              style={{
                width: '14px',
                height: '2px',
                borderTop: '2px dashed #ef4444',
                display: 'inline-block',
              }}
            />
            <span style={{ color: 'var(--text-primary)' }}>┄ Invalidated / Blocked Route</span>
          </div>
        </>
      )}

      {visibleLayers.incidents && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span
            style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: '#f59e0b',
              display: 'inline-block',
            }}
          />
          <span style={{ color: 'var(--text-primary)' }}>● Incident Report</span>
        </div>
      )}

      {visibleLayers.facilities && (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ color: '#ef4444', fontWeight: 'bold' }}>✚</span>
            <span style={{ color: 'var(--text-primary)' }}>Hospital / Trauma</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ color: '#10b981', fontWeight: 'bold' }}>⛺</span>
            <span style={{ color: 'var(--text-primary)' }}>Relief Shelter</span>
          </div>
        </>
      )}

      {visibleLayers.bridges && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ color: '#94a3b8', fontWeight: 'bold' }}>☵</span>
          <span style={{ color: 'var(--text-primary)' }}>Bridge Crossing</span>
        </div>
      )}
    </div>
  );
};
