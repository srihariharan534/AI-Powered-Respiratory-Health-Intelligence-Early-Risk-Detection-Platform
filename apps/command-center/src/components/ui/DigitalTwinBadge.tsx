import React from 'react';
import { StateVersionInfo } from '../../types';

interface DigitalTwinBadgeProps {
  versionInfo: StateVersionInfo;
}

export const DigitalTwinBadge: React.FC<DigitalTwinBadgeProps> = ({ versionInfo }) => {
  const hasVersion = versionInfo.version !== null && versionInfo.version !== undefined;

  return (
    <div
      className="digital-twin-badge"
      title={`Authority: ${versionInfo.authority}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.5rem',
        padding: '0.25rem 0.6rem',
        backgroundColor: 'var(--bg-surface-raised)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '4px',
        fontSize: '0.72rem',
        fontFamily: 'var(--font-mono)',
      }}
    >
      <span style={{ color: 'var(--text-muted)' }}>State Version:</span>
      <span
        style={{
          fontWeight: 700,
          color: hasVersion ? '#60a5fa' : 'var(--text-muted)',
        }}
      >
        {hasVersion ? versionInfo.version : '—'}
      </span>
    </div>
  );
};
