import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useI18n } from '../../context/I18nContext';
import { useFieldApp } from '../../context/FieldAppContext';
import { SyncQueueService } from '../../services/sync/syncQueueService';
import { ResourceRequestRepository } from '../../database/repositories/ResourceRequestRepository';
import { DurableResourceRequest } from '../../database/types';
import { ResourceRequest } from '../../types';

export const ResourceRequestScreen: React.FC = () => {
  const { t } = useI18n();
  const { connectionStatus } = useFieldApp();
  const navigate = useNavigate();

  const [resourceType, setResourceType] = useState<ResourceRequest['resource_type']>('RESCUE_BOAT');
  const [quantity, setQuantity] = useState<number>(2);
  const [urgency, setUrgency] = useState<ResourceRequest['urgency']>('HIGH');
  const [reason, setReason] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;

    setError(null);
    if (!reason.trim()) {
      setError('Operational reason is required for supply dispatch.');
      return;
    }

    const requestId = `REQ-${Date.now()}`;
    const durableReq: DurableResourceRequest = {
      request_id: requestId,
      resource_type: resourceType,
      quantity: Number(quantity),
      urgency: urgency,
      location: [80.2230, 13.0180],
      reason: reason.trim(),
      requested_by: 'FIELD_OFFICER_01',
      requested_at: new Date().toISOString(),
      status: 'PENDING_SYNC',
      local_record_id: `LOCAL-REQ-${Date.now()}`,
      created_locally_at: new Date().toISOString(),
      sync_status: 'PENDING_SYNC',
      sync_attempts: 0,
    };

    setIsSubmitting(true);

    try {
      // 1. Enqueue into outbox / sync queue immediately
      SyncQueueService.enqueue('RESOURCE_REQUEST', durableReq);

      // 2. Persist to durable IndexedDB resource request store
      const repo = new ResourceRequestRepository();
      await repo.save(durableReq);

      setSubmitted(true);
      setTimeout(() => {
        navigate('/sync');
      }, 1200);
    } catch (err: any) {
      console.error('Failed to save resource request to IndexedDB:', err);
      setError(`Storage Error: Could not save request on device (${err.message || 'IndexedDB error'}).`);
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0 }}>
          {t('action_resource_request')}
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

      {submitted && (
        <div
          style={{
            padding: '0.75rem',
            backgroundColor: 'rgba(34, 197, 94, 0.2)',
            border: '1px solid #22c55e',
            borderRadius: '6px',
            color: '#22c55e',
            fontSize: '0.85rem',
            fontWeight: 600,
          }}
        >
          ✓ {connectionStatus === 'OFFLINE' ? 'Saved on Device — Pending Sync' : 'Supply request queued for sync.'}
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

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
          <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Asset / Supply Category:
          </label>
          <select
            value={resourceType}
            onChange={(e) => setResourceType(e.target.value as ResourceRequest['resource_type'])}
          >
            <option value="RESCUE_BOAT">Inflatable Rescue Boat / Dinghy</option>
            <option value="MEDICAL_KIT">Emergency Trauma Medical Kits</option>
            <option value="FOOD_WATER">Potable Water & Emergency Rations</option>
            <option value="SQUAD_BACKUP">Search & Rescue Personnel Backup</option>
            <option value="AMBULANCE">Off-Road Evacuation Ambulance</option>
            <option value="SANDBAGS">Barrier Sandbags</option>
          </select>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
              Quantity Required:
            </label>
            <input
              type="number"
              min="1"
              max="50"
              value={quantity}
              onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
            />
          </div>

          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
              Urgency Level:
            </label>
            <select
              value={urgency}
              onChange={(e) => setUrgency(e.target.value as ResourceRequest['urgency'])}
            >
              <option value="IMMEDIATE">IMMEDIATE (Threat to Life)</option>
              <option value="HIGH">HIGH (Escalating)</option>
              <option value="ROUTINE">ROUTINE (Staging)</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
          <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Operational Justification:
          </label>
          <textarea
            required
            rows={3}
            placeholder="State why assets are required and current civilian status..."
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          style={{
            padding: '1rem',
            backgroundColor: isSubmitting ? 'var(--bg-card)' : 'var(--color-brand)',
            color: '#fff',
            border: 'none',
            fontSize: '1rem',
            fontWeight: 800,
            marginTop: '0.5rem',
            cursor: isSubmitting ? 'not-allowed' : 'pointer',
          }}
        >
          {isSubmitting
            ? 'Saving on Device...'
            : connectionStatus === 'OFFLINE'
            ? 'Save on Device'
            : t('btn_submit')}
        </button>
      </form>
    </div>
  );
};
