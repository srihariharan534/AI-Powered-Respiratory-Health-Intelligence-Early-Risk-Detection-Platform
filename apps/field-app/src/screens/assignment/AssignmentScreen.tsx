import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useFieldApp } from '../../context/FieldAppContext';
import { useI18n } from '../../context/I18nContext';
import { SyncQueueService } from '../../services/sync/syncQueueService';

export const AssignmentScreen: React.FC = () => {
  const { currentAssignment, updateAssignmentStatus } = useFieldApp();
  const { t } = useI18n();
  const navigate = useNavigate();

  if (!currentAssignment) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', backgroundColor: 'var(--bg-surface)', borderRadius: '12px' }}>
        <p style={{ color: 'var(--text-muted)' }}>{t('no_active_assignment')}</p>
        <button
          onClick={() => navigate('/')}
          style={{
            marginTop: '1rem',
            padding: '0.5rem 1rem',
            backgroundColor: 'var(--bg-card)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          ← Return Home
        </button>
      </div>
    );
  }

  const handleStatusChange = (newStatus: typeof currentAssignment.status) => {
    updateAssignmentStatus(newStatus);
    SyncQueueService.enqueue('STATUS_UPDATE', {
      assignment_id: currentAssignment.assignment_id,
      status: newStatus,
      updated_at: new Date().toISOString(),
    });
  };

  const statuses: Array<typeof currentAssignment.status> = [
    'ASSIGNED',
    'EN_ROUTE',
    'ON_SCENE',
    'COMPLETED',
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0 }}>
          {t('action_my_assignment')}
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
          ✕ Back
        </button>
      </div>

      {/* Assignment Card */}
      <div
        style={{
          padding: '1.25rem',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: '12px',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-brand)' }}>
            MISSION ID: {currentAssignment.assignment_id}
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

        <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
          {currentAssignment.task_name}
        </h2>

        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.4, margin: 0 }}>
          {currentAssignment.instructions}
        </p>

        {/* Location Target */}
        <div
          style={{
            backgroundColor: 'var(--bg-card)',
            padding: '0.75rem',
            borderRadius: '8px',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.8rem',
          }}
        >
          <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
            📍 Target Area: {currentAssignment.location.name}
          </div>
          <div style={{ color: 'var(--text-muted)', fontFamily: 'monospace', fontSize: '0.75rem' }}>
            Coordinates: [{currentAssignment.location.longitude.toFixed(5)}, {currentAssignment.location.latitude.toFixed(5)}]
          </div>
        </div>
      </div>

      {/* Interactive Status Stepper */}
      <div
        style={{
          backgroundColor: 'var(--bg-surface)',
          padding: '1rem',
          borderRadius: '12px',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
          Update Operational Progress:
        </span>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.75rem' }}>
          {statuses.map((status) => {
            const isCurrent = currentAssignment.status === status;
            return (
              <button
                key={status}
                type="button"
                onClick={() => handleStatusChange(status)}
                style={{
                  padding: '0.75rem 1rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  backgroundColor: isCurrent ? 'var(--color-brand)' : 'var(--bg-card)',
                  color: isCurrent ? '#fff' : 'var(--text-primary)',
                  border: `1px solid ${isCurrent ? 'transparent' : 'var(--border-subtle)'}`,
                  borderRadius: '8px',
                  fontWeight: isCurrent ? 700 : 500,
                  fontSize: '0.85rem',
                }}
              >
                <span>{status.replace('_', ' ')}</span>
                {isCurrent && <span style={{ fontSize: '0.75rem', opacity: 0.9 }}>CURRENT</span>}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tactical Quick Links */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
        <button
          onClick={() => navigate('/map')}
          style={{
            minHeight: '44px',
            backgroundColor: 'var(--bg-card)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.85rem',
            fontWeight: 600,
          }}
        >
          🗺️ View Map
        </button>
        <button
          onClick={() => navigate('/report')}
          style={{
            minHeight: '44px',
            backgroundColor: 'var(--bg-card)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.85rem',
            fontWeight: 600,
          }}
        >
          ▲ Report Incident
        </button>
      </div>
    </div>
  );
};
