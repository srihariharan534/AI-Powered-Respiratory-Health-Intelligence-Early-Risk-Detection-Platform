import React from 'react';
import { DataMode } from '../../types';

interface DataModeBadgeProps {
  mode: DataMode;
  onToggle?: () => void;
}

export const DataModeBadge: React.FC<DataModeBadgeProps> = ({ mode, onToggle }) => {
  const getConfig = () => {
    switch (mode) {
      case 'REAL':
        return {
          label: 'REAL DATA',
          bg: 'rgba(16, 185, 129, 0.15)',
          color: 'var(--color-online)',
          border: 'rgba(16, 185, 129, 0.4)',
        };
      case 'SIMULATION':
        return {
          label: 'SIMULATION',
          bg: 'rgba(139, 92, 246, 0.2)',
          color: '#a78bfa',
          border: '#8b5cf6',
        };
      case 'DEMO':
        return {
          label: 'DEMO MODE',
          bg: 'rgba(245, 158, 11, 0.15)',
          color: 'var(--color-degraded)',
          border: 'rgba(245, 158, 11, 0.4)',
        };
      case 'UNKNOWN':
      default:
        return {
          label: 'UNKNOWN MODE',
          bg: 'rgba(100, 116, 139, 0.2)',
          color: 'var(--text-muted)',
          border: 'var(--text-muted)',
        };
    }
  };

  const config = getConfig();

  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={!onToggle}
      className="data-mode-badge"
      aria-label={`Current Data Mode: ${config.label}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.4rem',
        padding: '0.25rem 0.6rem',
        borderRadius: '4px',
        fontSize: '0.72rem',
        fontWeight: 700,
        letterSpacing: '0.05em',
        backgroundColor: config.bg,
        color: config.color,
        border: `1px solid ${config.border}`,
        cursor: onToggle ? 'pointer' : 'default',
        outline: 'none',
      }}
    >
      <span
        style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: config.color,
        }}
      />
      {config.label}
    </button>
  );
};
