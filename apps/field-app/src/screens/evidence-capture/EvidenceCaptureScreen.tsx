import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useI18n } from '../../context/I18nContext';
import { useFieldApp } from '../../context/FieldAppContext';
import { SyncQueueService } from '../../services/sync/syncQueueService';
import { EvidenceRepository } from '../../database/repositories/EvidenceRepository';
import { DurableEvidence } from '../../database/types';
import { IncidentEvidenceItem } from '../../types';

export const EvidenceCaptureScreen: React.FC = () => {
  const { t } = useI18n();
  const { connectionStatus } = useFieldApp();
  const navigate = useNavigate();

  const [evidenceList, setEvidenceList] = useState<DurableEvidence[]>([]);
  const [evidenceDescription, setEvidenceDescription] = useState<string>('');
  const [evidenceType, setEvidenceType] = useState<IncidentEvidenceItem['type']>('photo');
  const [previewName, setPreviewName] = useState<string | null>(null);
  const [isQueueing, setIsQueueing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSimulatedCapture = () => {
    const item: DurableEvidence = {
      evidence_id: `EVD-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
      type: evidenceType,
      file_name: `field_capture_${Date.now()}.${evidenceType === 'photo' ? 'jpg' : 'mp4'}`,
      file_size: 1024 * 350, // 350 KB
      mime_type: evidenceType === 'photo' ? 'image/jpeg' : 'video/mp4',
      captured_at: new Date().toISOString(),
      description: evidenceDescription || 'Ground watermark gauge measurement',
      sync_status: 'PENDING_SYNC',
      local_record_id: `LOCAL-EVD-${Date.now()}`,
    };

    setEvidenceList([...evidenceList, item]);
    setPreviewName(item.file_name || null);
    setEvidenceDescription('');
  };

  const handleQueueAll = async () => {
    if (evidenceList.length === 0) {
      alert('Capture at least one evidence item before queueing.');
      return;
    }
    if (isQueueing) return;

    setIsQueueing(true);
    setError(null);

    try {
      const evidenceRepo = new EvidenceRepository();
      // 1. Persist each evidence item into IndexedDB evidence store
      for (const item of evidenceList) {
        await evidenceRepo.save(item);
      }

      // 2. Enqueue into sync queue & outbox
      SyncQueueService.enqueue('EVIDENCE', {
        incident_id: 'INC-DEFAULT-001',
        items: evidenceList,
      });

      alert(`${evidenceList.length} evidence records saved on device & attached to sync queue.`);
      navigate('/sync');
    } catch (err: any) {
      console.error('Failed to save evidence to IndexedDB:', err);
      setError(`Storage Error: Could not save evidence on device (${err.message || 'IndexedDB error'}).`);
      setIsQueueing(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0 }}>
          {t('action_capture_evidence')}
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
          ✕ Cancel
        </button>
      </div>

      {connectionStatus === 'OFFLINE' && (
        <div
          style={{
            padding: '0.6rem 0.8rem',
            backgroundColor: 'rgba(234, 179, 8, 0.15)',
            border: '1px solid rgba(234, 179, 8, 0.3)',
            borderRadius: '6px',
            color: '#eab308',
            fontSize: '0.75rem',
            lineHeight: 1.4,
          }}
        >
          {t('offline_notice')}
        </div>
      )}

      {error && (
        <div
          style={{
            padding: '0.75rem',
            backgroundColor: 'rgba(239, 68, 68, 0.2)',
            border: '1px solid #ef4444',
            borderRadius: '6px',
            color: '#ef4444',
            fontSize: '0.85rem',
            fontWeight: 600,
          }}
        >
          ⚠ {error}
        </div>
      )}

      <div style={{ backgroundColor: 'var(--bg-surface)', padding: '1rem', borderRadius: '10px', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            type="button"
            onClick={() => setEvidenceType('photo')}
            style={{
              flex: 1,
              minHeight: '40px',
              backgroundColor: evidenceType === 'photo' ? 'var(--color-brand)' : 'var(--bg-card)',
              color: '#fff',
              border: 'none',
              fontSize: '0.8rem',
              fontWeight: 700,
            }}
          >
            📷 Photo Capture
          </button>
          <button
            type="button"
            onClick={() => setEvidenceType('video')}
            style={{
              flex: 1,
              minHeight: '40px',
              backgroundColor: evidenceType === 'video' ? 'var(--color-brand)' : 'var(--bg-card)',
              color: '#fff',
              border: 'none',
              fontSize: '0.8rem',
              fontWeight: 700,
            }}
          >
            🎥 Short Clip
          </button>
        </div>

        <input
          type="text"
          placeholder="Evidence observation note (e.g. 50cm road flooding)"
          value={evidenceDescription}
          onChange={(e) => setEvidenceDescription(e.target.value)}
        />

        <button
          type="button"
          onClick={handleSimulatedCapture}
          style={{
            backgroundColor: 'var(--bg-card)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-subtle)',
            fontWeight: 700,
            fontSize: '0.9rem',
          }}
        >
          + Capture / Select File
        </button>

        {previewName && (
          <div style={{ padding: '0.5rem', backgroundColor: 'var(--bg-card)', borderRadius: '6px', fontSize: '0.75rem', color: '#22c55e' }}>
            ✓ Captured: <code>{previewName}</code>
          </div>
        )}
      </div>

      {evidenceList.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
            Attached Items ({evidenceList.length}):
          </span>
          {evidenceList.map((item, idx) => (
            <div
              key={idx}
              style={{
                padding: '0.75rem',
                backgroundColor: 'var(--bg-surface)',
                borderRadius: '8px',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: 600 }}>{item.file_name}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{item.description}</div>
              </div>
              <span style={{ fontSize: '0.7rem', color: 'var(--color-brand)', fontWeight: 600 }}>READY</span>
            </div>
          ))}

          <button
            onClick={handleQueueAll}
            disabled={isQueueing}
            style={{
              padding: '0.85rem',
              backgroundColor: isQueueing ? 'var(--bg-card)' : 'var(--color-success)',
              color: '#fff',
              border: 'none',
              fontWeight: 700,
              fontSize: '0.9rem',
              marginTop: '0.5rem',
              cursor: isQueueing ? 'not-allowed' : 'pointer',
            }}
          >
            {isQueueing ? 'Saving on Device...' : 'Save on Device & Queue'}
          </button>
        </div>
      )}
    </div>
  );
};
