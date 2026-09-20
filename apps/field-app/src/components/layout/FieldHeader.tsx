import React from 'react';
import { useFieldApp } from '../../context/FieldAppContext';
import { useI18n } from '../../context/I18nContext';
import { OfflineIndicator } from '../offline-indicator/OfflineIndicator';

export const FieldHeader: React.FC = () => {
  const { connectionStatus, pendingSyncCount } = useFieldApp();
  const { locale, setLocale } = useI18n();

  return (
    <header
      style={{
        height: 'var(--header-height)',
        backgroundColor: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 1rem',
        maxWidth: '600px',
        margin: '0 auto',
        width: '100%',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--color-brand)' }}>NEXUS</span>
        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
          FIELD
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <button
          onClick={() => setLocale(locale === 'en' ? 'ta' : 'en')}
          style={{
            padding: '0.2rem 0.5rem',
            minHeight: '32px',
            fontSize: '0.75rem',
            fontWeight: 700,
            backgroundColor: 'var(--bg-card)',
            color: 'var(--text-secondary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '4px',
          }}
          aria-label="Toggle language between English and Tamil"
        >
          {locale === 'en' ? 'தமிழ்' : 'EN'}
        </button>

        <OfflineIndicator status={connectionStatus} pendingCount={pendingSyncCount} />
      </div>
    </header>
  );
};
