import React from 'react';
import { ConnectionStatus } from '../../types';
import { useI18n } from '../../context/I18nContext';

interface OfflineIndicatorProps {
  status: ConnectionStatus;
  pendingCount?: number;
}

export const OfflineIndicator: React.FC<OfflineIndicatorProps> = ({ status, pendingCount = 0 }) => {
  const { t } = useI18n();

  const getStatusConfig = () => {
    switch (status) {
      case 'ONLINE':
        return {
          label: t('status_online'),
          icon: '●',
          bg: 'rgba(34, 197, 94, 0.2)',
          border: '#22c55e',
          color: '#22c55e',
        };
      case 'OFFLINE':
        return {
          label: t('status_offline'),
          icon: '○',
          bg: 'rgba(239, 68, 68, 0.2)',
          border: '#ef4444',
          color: '#ef4444',
        };
      case 'SYNCING':
        return {
          label: t('status_syncing'),
          icon: '⟳',
          bg: 'rgba(59, 130, 246, 0.2)',
          border: '#3b82f6',
          color: '#3b82f6',
        };
      case 'SYNC_ERROR':
        return {
          label: t('status_sync_error'),
          icon: '⚠',
          bg: 'rgba(234, 179, 8, 0.2)',
          border: '#eab308',
          color: '#eab308',
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div
      role="status"
      aria-label={`Connectivity status: ${config.label}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.4rem',
        padding: '0.25rem 0.6rem',
        borderRadius: '16px',
        backgroundColor: config.bg,
        border: `1px solid ${config.border}`,
        color: config.color,
        fontSize: '0.75rem',
        fontWeight: 700,
        letterSpacing: '0.02em',
      }}
    >
      <span aria-hidden="true" style={{ fontSize: '0.85rem' }}>{config.icon}</span>
      <span>{config.label}</span>
      {pendingCount > 0 && (
        <span
          style={{
            marginLeft: '0.2rem',
            padding: '0.1rem 0.35rem',
            backgroundColor: 'var(--bg-primary)',
            borderRadius: '10px',
            fontSize: '0.7rem',
          }}
        >
          {pendingCount}
        </span>
      )}
    </div>
  );
};
