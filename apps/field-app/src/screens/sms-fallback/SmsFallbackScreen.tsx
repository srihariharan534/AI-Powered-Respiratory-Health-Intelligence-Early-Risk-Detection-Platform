import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useI18n } from '../../context/I18nContext';
import { useFieldApp } from '../../context/FieldAppContext';
import { IncidentSeverity } from '../../types';

export const SmsFallbackScreen: React.FC = () => {
  const { t } = useI18n();
  const { currentAssignment } = useFieldApp();
  const navigate = useNavigate();

  const [entityId, setEntityId] = useState<string>(currentAssignment?.incident_id || 'INC-001');
  const [status, setStatus] = useState<string>('ACTIVE');
  const [severity, setSeverity] = useState<IncidentSeverity>('CRITICAL');
  const [lon, setLon] = useState<string>('80.2230');
  const [lat, setLat] = useState<string>('13.0180');
  const [copied, setCopied] = useState<boolean>(false);

  // Phase 04 format: FLOOD <ENTITY_ID> <STATUS> <SEVERITY> <LAT> <LON>
  const formattedSms = `FLOOD ${entityId} ${status} ${severity} ${parseFloat(lat).toFixed(5)} ${parseFloat(lon).toFixed(5)}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(formattedSms);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0 }}>
          {t('action_sms_fallback')}
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

      <div
        style={{
          padding: '0.75rem 1rem',
          backgroundColor: 'rgba(234, 179, 8, 0.15)',
          border: '1px solid rgba(234, 179, 8, 0.3)',
          borderRadius: '8px',
          color: '#eab308',
          fontSize: '0.75rem',
          lineHeight: 1.4,
        }}
      >
        ⚠ {t('sms_disclaimer')}
      </div>

      {/* Structured Output Preview */}
      <div
        style={{
          backgroundColor: 'var(--bg-surface)',
          padding: '1.25rem',
          borderRadius: '12px',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
            Phase 04 SMS Payload (≤160 Chars):
          </span>
          <span
            style={{
              fontSize: '0.7rem',
              fontWeight: 700,
              color: formattedSms.length <= 160 ? '#22c55e' : '#ef4444',
            }}
          >
            {formattedSms.length}/160 chars
          </span>
        </div>

        <div
          style={{
            backgroundColor: '#090d16',
            padding: '1rem',
            borderRadius: '8px',
            fontFamily: 'monospace',
            fontSize: '1rem',
            color: '#38bdf8',
            wordBreak: 'break-all',
            border: '1px solid var(--border-subtle)',
          }}
        >
          {formattedSms}
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            type="button"
            onClick={handleCopy}
            style={{
              flex: 1,
              minHeight: '44px',
              backgroundColor: copied ? '#22c55e' : 'var(--bg-card)',
              color: '#fff',
              border: '1px solid var(--border-subtle)',
              fontWeight: 700,
              fontSize: '0.85rem',
            }}
          >
            {copied ? '✓ Copied!' : `📋 ${t('btn_copy')}`}
          </button>
          <a
            href={`sms:?body=${encodeURIComponent(formattedSms)}`}
            style={{
              flex: 1,
              minHeight: '44px',
              backgroundColor: 'var(--color-brand)',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              textDecoration: 'none',
              borderRadius: '8px',
              fontWeight: 700,
              fontSize: '0.85rem',
            }}
          >
            💬 Open SMS App
          </a>
        </div>
      </div>

      {/* SMS Param Editor */}
      <div
        style={{
          backgroundColor: 'var(--bg-surface)',
          padding: '1rem',
          borderRadius: '12px',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
        }}
      >
        <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
          Broadcast Parameters:
        </span>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
            <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Entity / Incident ID:</label>
            <input
              type="text"
              value={entityId}
              onChange={(e) => setEntityId(e.target.value.toUpperCase())}
            />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
            <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Status:</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="ACTIVE">ACTIVE</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="RESOLVED">RESOLVED</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
          <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Severity Tier:</label>
          <select value={severity} onChange={(e) => setSeverity(e.target.value as IncidentSeverity)}>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
            <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Latitude:</label>
            <input type="text" value={lat} onChange={(e) => setLat(e.target.value)} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
            <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Longitude:</label>
            <input type="text" value={lon} onChange={(e) => setLon(e.target.value)} />
          </div>
        </div>
      </div>
    </div>
  );
};
