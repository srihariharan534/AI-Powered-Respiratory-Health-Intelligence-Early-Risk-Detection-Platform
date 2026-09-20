import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useFieldApp } from '../../context/FieldAppContext';
import { useI18n } from '../../context/I18nContext';

export const CachedMapScreen: React.FC = () => {
  const { currentAssignment } = useFieldApp();
  const { t } = useI18n();
  const navigate = useNavigate();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0 }}>
          {t('action_cached_map')}
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
          ✕ Close
        </button>
      </div>

      {/* Offline Map Canvas Surface */}
      <div
        style={{
          position: 'relative',
          height: '320px',
          backgroundColor: '#0b1329',
          borderRadius: '12px',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
          padding: '1rem',
          textAlign: 'center',
        }}
      >
        {/* Subtle coordinate grid lines */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage:
              'linear-gradient(to right, rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.04) 1px, transparent 1px)',
            backgroundSize: '32px 32px',
          }}
        />

        <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ fontSize: '2.5rem' }}>🗺️</div>
          <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
            Vector Tile Foundation
          </div>
          <p
            style={{
              fontSize: '0.75rem',
              color: 'var(--text-muted)',
              maxWidth: '260px',
              margin: 0,
              lineHeight: 1.4,
            }}
          >
            OFFLINE MAP: Cached map tiles will be available when configured (Phase 23+).
          </p>

          {currentAssignment && (
            <div
              style={{
                marginTop: '0.5rem',
                backgroundColor: 'rgba(15, 23, 42, 0.9)',
                padding: '0.4rem 0.8rem',
                borderRadius: '6px',
                border: '1px solid var(--border-subtle)',
                fontSize: '0.75rem',
                fontFamily: 'monospace',
                color: '#38bdf8',
              }}
            >
              📍 Waypoint: [{currentAssignment.location.longitude.toFixed(4)}, {currentAssignment.location.latitude.toFixed(4)}]
            </div>
          )}
        </div>

        <div
          style={{
            position: 'absolute',
            bottom: '8px',
            right: '8px',
            fontSize: '0.65rem',
            fontFamily: 'monospace',
            color: 'var(--text-muted)',
          }}
        >
          WGS84 EPSG:4326
        </div>
      </div>

      {/* Layer Toggles (Mock controls for Phase 22) */}
      <div
        style={{
          backgroundColor: 'var(--bg-surface)',
          padding: '1rem',
          borderRadius: '12px',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.5rem',
        }}
      >
        <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
          Tactical Map Layers (Read-Only Preview):
        </span>

        <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem' }}>
          <span>🌊 Flood Inundation Contours</span>
          <input type="checkbox" defaultChecked disabled />
        </label>
        <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem' }}>
          <span>🏥 Relief Shelters & Hospitals</span>
          <input type="checkbox" defaultChecked disabled />
        </label>
        <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem' }}>
          <span>🚨 Active Ground Incidents</span>
          <input type="checkbox" defaultChecked disabled />
        </label>
        <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem' }}>
          <span>🛣️ Safe Evacuation Corridors</span>
          <input type="checkbox" defaultChecked disabled />
        </label>
      </div>
    </div>
  );
};
