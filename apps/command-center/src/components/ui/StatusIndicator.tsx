import React from 'react';
import { ConnectionStatus } from '../../types';

interface StatusIndicatorProps {
  status: ConnectionStatus;
  showText?: boolean;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status, showText = true }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'ONLINE':
        return {
          label: 'ONLINE',
          color: 'var(--color-online)',
          ariaLabel: 'System status: Online and connected',
        };
      case 'DEGRADED':
        return {
          label: 'DEGRADED',
          color: 'var(--color-degraded)',
          ariaLabel: 'System status: Degraded connectivity',
        };
      case 'OFFLINE':
      default:
        return {
          label: 'OFFLINE',
          color: 'var(--color-offline)',
          ariaLabel: 'System status: Offline',
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div
      className="status-indicator"
      role="status"
      aria-label={config.ariaLabel}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.4rem',
        fontSize: '0.75rem',
        fontWeight: 600,
        letterSpacing: '0.05em',
      }}
    >
      <span
        style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: config.color,
          boxShadow: `0 0 6px ${config.color}`,
        }}
      />
      {showText && <span>{config.label}</span>}
    </div>
  );
};
