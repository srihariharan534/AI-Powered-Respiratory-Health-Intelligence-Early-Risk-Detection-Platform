import React from 'react';
import { SeverityLevel } from '../../types';

interface SeverityBadgeProps {
  level: SeverityLevel;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ level }) => {
  const getConfig = () => {
    switch (level) {
      case 'CRITICAL':
        return { label: 'CRITICAL', bg: 'rgba(239, 68, 68, 0.15)', color: 'var(--color-critical)', border: 'var(--color-critical)' };
      case 'HIGH':
        return { label: 'HIGH', bg: 'rgba(249, 115, 22, 0.15)', color: 'var(--color-severe)', border: 'var(--color-severe)' };
      case 'MEDIUM':
        return { label: 'MEDIUM', bg: 'rgba(245, 158, 11, 0.15)', color: 'var(--color-moderate)', border: 'var(--color-moderate)' };
      case 'LOW':
        return { label: 'LOW', bg: 'rgba(56, 189, 248, 0.15)', color: 'var(--color-low)', border: 'var(--color-low)' };
      case 'UNKNOWN':
      default:
        return { label: 'UNKNOWN', bg: 'rgba(100, 116, 139, 0.15)', color: 'var(--text-muted)', border: 'var(--text-muted)' };
    }
  };

  const config = getConfig();

  return (
    <span
      className="severity-badge"
      role="status"
      aria-label={`Severity level: ${config.label}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '0.2rem 0.5rem',
        borderRadius: '4px',
        fontSize: '0.7rem',
        fontWeight: 700,
        letterSpacing: '0.05em',
        backgroundColor: config.bg,
        color: config.color,
        border: `1px solid ${config.border}`,
      }}
    >
      {config.label}
    </span>
  );
};
