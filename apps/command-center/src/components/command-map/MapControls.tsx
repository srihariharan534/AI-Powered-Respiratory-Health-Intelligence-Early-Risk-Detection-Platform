/**
 * Interactive Layer Controls for Command Map
 * Allows emergency coordinators to toggle flood hazards, roads, routes, incidents, and facilities.
 */

import React from 'react';

interface MapControlsProps {
  layers: {
    flood: boolean;
    roads: boolean;
    bridges: boolean;
    incidents: boolean;
    facilities: boolean;
    routes: boolean;
  };
  onToggleLayer: (layerName: keyof MapControlsProps['layers']) => void;
  onResetView: () => void;
}

export const MapControls: React.FC<MapControlsProps> = ({
  layers,
  onToggleLayer,
  onResetView,
}) => {
  return (
    <div
      className="map-controls"
      role="toolbar"
      aria-label="Map Layer Filters"
      style={{
        backgroundColor: 'rgba(17, 22, 34, 0.92)',
        backdropFilter: 'blur(6px)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '6px',
        padding: '0.6rem 0.75rem',
        fontSize: '0.72rem',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        gap: '0.6rem',
        boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
      }}
    >
      <span
        style={{
          fontWeight: 700,
          letterSpacing: '0.05em',
          textTransform: 'uppercase',
          color: 'var(--text-muted)',
          marginRight: '0.2rem',
        }}
      >
        Layers:
      </span>

      <button
        type="button"
        onClick={() => onToggleLayer('flood')}
        style={{
          padding: '0.25rem 0.6rem',
          borderRadius: '4px',
          border: '1px solid',
          borderColor: layers.flood ? '#ef4444' : 'var(--border-subtle)',
          backgroundColor: layers.flood ? 'rgba(239, 68, 68, 0.2)' : 'var(--bg-surface)',
          color: layers.flood ? '#fca5a5' : 'var(--text-muted)',
          cursor: 'pointer',
          fontWeight: 600,
        }}
      >
        ■ Flood Hazard
      </button>

      <button
        type="button"
        onClick={() => onToggleLayer('roads')}
        style={{
          padding: '0.25rem 0.6rem',
          borderRadius: '4px',
          border: '1px solid',
          borderColor: layers.roads ? '#10b981' : 'var(--border-subtle)',
          backgroundColor: layers.roads ? 'rgba(16, 185, 129, 0.2)' : 'var(--bg-surface)',
          color: layers.roads ? '#6ee7b7' : 'var(--text-muted)',
          cursor: 'pointer',
          fontWeight: 600,
        }}
      >
        ━ Roads
      </button>

      <button
        type="button"
        onClick={() => onToggleLayer('routes')}
        style={{
          padding: '0.25rem 0.6rem',
          borderRadius: '4px',
          border: '1px solid',
          borderColor: layers.routes ? '#3b82f6' : 'var(--border-subtle)',
          backgroundColor: layers.routes ? 'rgba(59, 130, 246, 0.2)' : 'var(--bg-surface)',
          color: layers.routes ? '#93c5fd' : 'var(--text-muted)',
          cursor: 'pointer',
          fontWeight: 600,
        }}
      >
        ━ Dynamic Routes
      </button>

      <button
        type="button"
        onClick={() => onToggleLayer('incidents')}
        style={{
          padding: '0.25rem 0.6rem',
          borderRadius: '4px',
          border: '1px solid',
          borderColor: layers.incidents ? '#f59e0b' : 'var(--border-subtle)',
          backgroundColor: layers.incidents ? 'rgba(245, 158, 11, 0.2)' : 'var(--bg-surface)',
          color: layers.incidents ? '#fcd34d' : 'var(--text-muted)',
          cursor: 'pointer',
          fontWeight: 600,
        }}
      >
        ● Incidents
      </button>

      <button
        type="button"
        onClick={() => onToggleLayer('facilities')}
        style={{
          padding: '0.25rem 0.6rem',
          borderRadius: '4px',
          border: '1px solid',
          borderColor: layers.facilities ? '#8b5cf6' : 'var(--border-subtle)',
          backgroundColor: layers.facilities ? 'rgba(139, 92, 246, 0.2)' : 'var(--bg-surface)',
          color: layers.facilities ? '#c4b5fd' : 'var(--text-muted)',
          cursor: 'pointer',
          fontWeight: 600,
        }}
      >
        ✚ Facilities
      </button>

      <button
        type="button"
        onClick={() => onToggleLayer('bridges')}
        style={{
          padding: '0.25rem 0.6rem',
          borderRadius: '4px',
          border: '1px solid',
          borderColor: layers.bridges ? '#64748b' : 'var(--border-subtle)',
          backgroundColor: layers.bridges ? 'rgba(100, 116, 139, 0.2)' : 'var(--bg-surface)',
          color: layers.bridges ? '#cbd5e1' : 'var(--text-muted)',
          cursor: 'pointer',
          fontWeight: 600,
        }}
      >
        ☵ Bridges
      </button>

      <button
        type="button"
        onClick={onResetView}
        title="Reset map view to center of command sector"
        style={{
          marginLeft: 'auto',
          padding: '0.25rem 0.6rem',
          borderRadius: '4px',
          border: '1px solid var(--border-strong)',
          backgroundColor: 'var(--bg-surface-raised)',
          color: 'var(--text-primary)',
          cursor: 'pointer',
          fontWeight: 600,
        }}
      >
        ⌖ Reset Center
      </button>
    </div>
  );
};
