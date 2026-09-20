import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useFieldApp } from '../../context/FieldAppContext';
import { useI18n } from '../../context/I18nContext';
import { SyncQueueService } from '../../services/sync/syncQueueService';

export const SyncStatusScreen: React.FC = () => {
  const { t } = useI18n();
  const {
    connectionStatus,
    pendingItems,
    swStatus,
    hasSwUpdate,
    applySwUpdate,
    bgSyncCapability,
  } = useFieldApp();
  const navigate = useNavigate();

  const [isSyncing, setIsSyncing] = React.useState<boolean>(false);
  const [syncFeedback, setSyncFeedback] = React.useState<string | null>(null);

  const handleManualSync = async () => {
    if (connectionStatus === 'OFFLINE') {
      alert('Cannot sync while device is in OFFLINE mode.');
      return;
    }
    setIsSyncing(true);
    setSyncFeedback(null);
    try {
      const summary = await SyncQueueService.triggerSync();
      setSyncFeedback(
        `Sync completed: ${summary.accepted} accepted, ${summary.duplicates} duplicates, ${summary.conflicts} conflicts, ${summary.rejected} rejected.`
      );
    } catch (err: any) {
      setSyncFeedback(`Sync failed: ${err.message || 'Unknown network error'}`);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleClear = () => {
    if (confirm('Clear local pending queue? (Development / Testing only)')) {
      SyncQueueService.clearQueue();
    }
  };

  // Real store breakdown from durable outbox items
  const incidentCount = pendingItems.filter((i) => i.entity_type === 'INCIDENT').length;
  const evidenceCount = pendingItems.filter((i) => i.entity_type === 'EVIDENCE').length;
  const resourceCount = pendingItems.filter((i) => i.entity_type === 'RESOURCE_REQUEST').length;
  const statusCount = pendingItems.filter((i) => i.entity_type === 'STATUS_UPDATE').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0 }}>
          {t('action_sync_status')}
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

      {/* Network & Queue Health Banner */}
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
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Network Connection:
          </span>
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              padding: '0.2rem 0.6rem',
              borderRadius: '12px',
              backgroundColor:
                connectionStatus === 'ONLINE'
                  ? 'rgba(34, 197, 94, 0.2)'
                  : connectionStatus === 'OFFLINE'
                  ? 'rgba(239, 68, 68, 0.2)'
                  : 'rgba(56, 189, 248, 0.2)',
              color:
                connectionStatus === 'ONLINE'
                  ? '#22c55e'
                  : connectionStatus === 'OFFLINE'
                  ? '#ef4444'
                  : '#38bdf8',
            }}
          >
            {connectionStatus}
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Total Pending Operations (IndexedDB):
          </span>
          <span style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            {pendingItems.length}
          </span>
        </div>

        {/* Category Breakdown */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '0.4rem',
            textAlign: 'center',
            backgroundColor: 'var(--bg-card)',
            padding: '0.6rem',
            borderRadius: '8px',
            fontSize: '0.75rem',
          }}
        >
          <div>
            <div style={{ fontWeight: 800, color: 'var(--text-primary)' }}>{incidentCount}</div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Incidents</div>
          </div>
          <div>
            <div style={{ fontWeight: 800, color: 'var(--text-primary)' }}>{evidenceCount}</div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Evidence</div>
          </div>
          <div>
            <div style={{ fontWeight: 800, color: 'var(--text-primary)' }}>{resourceCount}</div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Resources</div>
          </div>
          <div>
            <div style={{ fontWeight: 800, color: 'var(--text-primary)' }}>{statusCount}</div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Updates</div>
          </div>
        </div>

        {syncFeedback && (
          <div
            style={{
              padding: '0.6rem',
              borderRadius: '6px',
              backgroundColor: syncFeedback.includes('failed') ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.2)',
              color: syncFeedback.includes('failed') ? '#ef4444' : '#22c55e',
              fontSize: '0.75rem',
              fontWeight: 600,
            }}
          >
            {syncFeedback}
          </div>
        )}

        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
          <button
            type="button"
            onClick={handleManualSync}
            disabled={isSyncing || connectionStatus === 'OFFLINE' || pendingItems.length === 0}
            style={{
              flex: 1,
              minHeight: '42px',
              backgroundColor: isSyncing ? 'var(--bg-card)' : 'var(--color-brand)',
              color: '#fff',
              border: 'none',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: isSyncing ? 'not-allowed' : 'pointer',
            }}
          >
            {isSyncing ? 'Synchronizing with Central Authority...' : t('btn_retry')}
          </button>
          <button
            type="button"
            onClick={handleClear}
            disabled={pendingItems.length === 0}
            style={{
              padding: '0 1rem',
              minHeight: '42px',
              backgroundColor: 'var(--bg-card)',
              color: 'var(--text-muted)',
              border: '1px solid var(--border-subtle)',
              fontSize: '0.8rem',
            }}
          >
            Reset (Dev)
          </button>
        </div>
      </div>

      {/* Service Worker & Background Sync Diagnostic Cards */}
      <div
        style={{
          padding: '1rem',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: '12px',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.6rem',
        }}
      >
        <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
          Offline Runtime & Engine State:
        </span>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem' }}>
          <span>Service Worker Runtime:</span>
          <span
            style={{
              fontWeight: 700,
              color: swStatus === 'ACTIVE' ? '#22c55e' : swStatus === 'WAITING' ? '#eab308' : 'var(--text-muted)',
            }}
          >
            {swStatus}
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem' }}>
          <span>Background Sync Foundation:</span>
          <span
            style={{
              fontWeight: 700,
              color: bgSyncCapability.isSupported ? '#22c55e' : 'var(--text-muted)',
            }}
          >
            {bgSyncCapability.isSupported ? 'SUPPORTED' : 'UNAVAILABLE (Browser Limit)'}
          </span>
        </div>

        {hasSwUpdate && (
          <div
            style={{
              marginTop: '0.4rem',
              padding: '0.6rem',
              backgroundColor: 'rgba(56, 189, 248, 0.15)',
              borderRadius: '8px',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span style={{ fontSize: '0.75rem', color: '#38bdf8', fontWeight: 600 }}>
              New NEXUS version ready
            </span>
            <button
              type="button"
              onClick={applySwUpdate}
              style={{
                padding: '0.3rem 0.6rem',
                backgroundColor: 'var(--color-brand)',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                fontSize: '0.75rem',
                fontWeight: 700,
              }}
            >
              Update App
            </button>
          </div>
        )}
      </div>

      {/* Queue Items List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
          Durable Outbox Queue ({pendingItems.length}):
        </span>

        {pendingItems.length === 0 ? (
          <div
            style={{
              padding: '2rem',
              textAlign: 'center',
              backgroundColor: 'var(--bg-surface)',
              borderRadius: '8px',
              color: 'var(--text-muted)',
              fontSize: '0.85rem',
            }}
          >
            ✓ All records synchronized or no local operations pending.
          </div>
        ) : (
          pendingItems.map((item) => (
            <div
              key={item.queue_id}
              style={{
                padding: '0.75rem 1rem',
                backgroundColor: 'var(--bg-surface)',
                borderRadius: '8px',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {item.entity_type}
                </div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  Op ID: {item.queue_id} • Saved: {new Date(item.queued_at).toLocaleTimeString()}
                </div>
              </div>

              <div>
                <span
                  style={{
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    padding: '0.2rem 0.5rem',
                    borderRadius: '4px',
                    backgroundColor:
                      item.status === 'ERROR'
                        ? 'rgba(239, 68, 68, 0.2)'
                        : item.status === 'QUEUED'
                        ? 'rgba(234, 179, 8, 0.2)'
                        : 'rgba(56, 189, 248, 0.2)',
                    color:
                      item.status === 'ERROR'
                        ? '#ef4444'
                        : item.status === 'QUEUED'
                        ? '#eab308'
                        : '#38bdf8',
                  }}
                >
                  {item.status}
                </span>
                {item.error_message && (
                  <div style={{ fontSize: '0.65rem', color: '#ef4444', marginTop: '0.25rem', maxWidth: '200px' }}>
                    {item.error_message}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
