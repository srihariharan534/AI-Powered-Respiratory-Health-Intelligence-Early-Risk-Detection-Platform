import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useFieldApp } from '../../context/FieldAppContext';
import { useI18n } from '../../context/I18nContext';

export const HomeScreen: React.FC = () => {
  const { currentAssignment, connectionStatus, setConnectionStatus } = useFieldApp();
  const { t } = useI18n();
  const navigate = useNavigate();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Tactical Assignment Banner */}
      {currentAssignment ? (
        <div
          onClick={() => navigate('/assignment')}
          style={{
            padding: '1rem',
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-strong)',
            borderRadius: '12px',
            cursor: 'pointer',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-brand)' }}>
              {t('assignment_title').toUpperCase()}
            </span>
            <span
              style={{
                fontSize: '0.7rem',
                fontWeight: 700,
                padding: '0.15rem 0.4rem',
                borderRadius: '4px',
                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                color: '#ef4444',
              }}
            >
              PRIORITY {currentAssignment.priority}
            </span>
          </div>
          <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 0.25rem 0' }}>
            {currentAssignment.task_name}
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: '0 0 0.5rem 0' }}>
            📍 {currentAssignment.location.name}
          </p>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            <span>Status: <strong style={{ color: 'var(--text-primary)' }}>{currentAssignment.status}</strong></span>
            <span style={{ color: 'var(--color-brand)' }}>View Details →</span>
          </div>
        </div>
      ) : (
        <div style={{ padding: '1rem', backgroundColor: 'var(--bg-surface)', borderRadius: '12px', textAlign: 'center' }}>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>{t('no_active_assignment')}</p>
        </div>
      )}

      {/* Primary Touch Actions Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
        <button
          onClick={() => navigate('/report')}
          style={{
            padding: '1rem',
            backgroundColor: 'var(--color-danger)',
            color: '#fff',
            border: 'none',
            borderRadius: '10px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.4rem',
            fontSize: '0.9rem',
            fontWeight: 700,
          }}
        >
          <span style={{ fontSize: '1.5rem' }}>▲</span>
          <span>{t('action_report_incident')}</span>
        </button>

        <button
          onClick={() => navigate('/evidence')}
          style={{
            padding: '1rem',
            backgroundColor: 'var(--bg-surface)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '10px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.4rem',
            fontSize: '0.9rem',
            fontWeight: 700,
          }}
        >
          <span style={{ fontSize: '1.5rem' }}>📷</span>
          <span>{t('action_capture_evidence')}</span>
        </button>

        <button
          onClick={() => navigate('/map')}
          style={{
            padding: '1rem',
            backgroundColor: 'var(--bg-surface)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '10px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.4rem',
            fontSize: '0.9rem',
            fontWeight: 700,
          }}
        >
          <span style={{ fontSize: '1.5rem' }}>🗺️</span>
          <span>{t('action_cached_map')}</span>
        </button>

        <button
          onClick={() => navigate('/resources')}
          style={{
            padding: '1rem',
            backgroundColor: 'var(--bg-surface)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '10px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.4rem',
            fontSize: '0.9rem',
            fontWeight: 700,
          }}
        >
          <span style={{ fontSize: '1.5rem' }}>📦</span>
          <span>{t('action_resource_request')}</span>
        </button>

        <button
          onClick={() => navigate('/sms')}
          style={{
            padding: '1rem',
            backgroundColor: 'var(--bg-surface)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '10px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.4rem',
            fontSize: '0.9rem',
            fontWeight: 700,
          }}
        >
          <span style={{ fontSize: '1.5rem' }}>💬</span>
          <span>{t('action_sms_fallback')}</span>
        </button>

        <button
          onClick={() => navigate('/sync')}
          style={{
            padding: '1rem',
            backgroundColor: 'var(--bg-surface)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '10px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.4rem',
            fontSize: '0.9rem',
            fontWeight: 700,
          }}
        >
          <span style={{ fontSize: '1.5rem' }}>⟳</span>
          <span>{t('action_sync_status')}</span>
        </button>
      </div>

      {/* Connectivity Simulation Bar (for Field Testing) */}
      <div
        style={{
          marginTop: 'auto',
          padding: '0.75rem',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
          fontSize: '0.75rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <span style={{ color: 'var(--text-muted)' }}>Field Connection Mode:</span>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={() => setConnectionStatus('ONLINE')}
            style={{
              padding: '0.2rem 0.5rem',
              minHeight: '28px',
              fontSize: '0.7rem',
              fontWeight: 700,
              backgroundColor: connectionStatus === 'ONLINE' ? '#22c55e' : 'var(--bg-card)',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
            }}
          >
            ONLINE
          </button>
          <button
            onClick={() => setConnectionStatus('OFFLINE')}
            style={{
              padding: '0.2rem 0.5rem',
              minHeight: '28px',
              fontSize: '0.7rem',
              fontWeight: 700,
              backgroundColor: connectionStatus === 'OFFLINE' ? '#ef4444' : 'var(--bg-card)',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
            }}
          >
            OFFLINE
          </button>
        </div>
      </div>
    </div>
  );
};
