import React from 'react';
import { useApp } from '../../context/AppContext';

export const Footer: React.FC = () => {
  const { lastSyncTime, stateVersionInfo, dataMode } = useApp();

  return (
    <footer className="footer-container" role="contentinfo">
      <div style={{ display: 'flex', gap: '1.25rem', alignItems: 'center' }}>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>AUTHORITY: </span>
          <span style={{ color: 'var(--text-secondary)' }}>{stateVersionInfo.authority || 'NEXUS-NODE-01'}</span>
        </div>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>VERSION: </span>
          <span style={{ color: '#60a5fa' }}>{stateVersionInfo.version ? `v${stateVersionInfo.version}` : 'v104'}</span>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>DATA TRUST: </span>
          <span style={{ color: 'var(--color-online)', fontWeight: 600 }}>● VERIFIED</span>
        </div>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>MODE: </span>
          <span style={{ color: dataMode === 'REAL' ? 'var(--color-online)' : '#a78bfa', fontWeight: 600 }}>
            {dataMode}
          </span>
        </div>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>LAST SYNC: </span>
          <span style={{ color: 'var(--text-secondary)' }}>
            {lastSyncTime ? lastSyncTime.toLocaleTimeString() : 'Nominal Stream'}
          </span>
        </div>
      </div>
    </footer>
  );
};
