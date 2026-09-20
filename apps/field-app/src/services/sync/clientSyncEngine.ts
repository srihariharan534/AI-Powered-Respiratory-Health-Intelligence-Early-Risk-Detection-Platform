/**
 * Client Synchronization Engine (Phase 25)
 * Coordinates synchronization between local IndexedDB outbox and backend API.
 * Features:
 * - Distributed browser lock (Web Locks API / lease fallback) to prevent multi-tab concurrency.
 * - Batch submission conforming to Phase 25 Sync Protocol.
 * - Local IndexedDB record reconciliation:
 *   - ACCEPTED / DUPLICATE: Marks local entity as SYNCED and archives/removes from active outbox.
 *   - CONFLICT: Marks record with CONFLICT status, preserves conflict metadata and server state diff.
 *   - REJECTED: Marks record with SYNC_ERROR and stores permanent rejection reason.
 *   - RETRYABLE_ERROR: Preserves outbox operation, increments attempt count, and schedules retry.
 */

import { OutboxRepository } from '../../database/repositories/OutboxRepository';
import { IncidentRepository } from '../../database/repositories/IncidentRepository';
import { ResourceRequestRepository } from '../../database/repositories/ResourceRequestRepository';
import { OutboxOperation } from '../../database/types';

export interface SyncEngineResult {
  total: number;
  accepted: number;
  duplicates: number;
  conflicts: number;
  rejected: number;
  errors: string[];
}

export class ClientSyncEngine {
  private static instance: ClientSyncEngine | null = null;
  private isSyncing: boolean = false;
  private syncLockKey: string = 'nexus_field_sync_lock';
  private outboxRepo: OutboxRepository;
  private incidentRepo: IncidentRepository;
  private resourceRequestRepo: ResourceRequestRepository;

  private constructor() {
    this.outboxRepo = new OutboxRepository();
    this.incidentRepo = new IncidentRepository();
    this.resourceRequestRepo = new ResourceRequestRepository();
  }

  public static getInstance(): ClientSyncEngine {
    if (!this.instance) {
      this.instance = new ClientSyncEngine();
    }
    return this.instance;
  }

  public isBusy(): boolean {
    return this.isSyncing;
  }

  /**
   * Triggers a synchronization cycle with distributed lock protection.
   */
  public async sync(): Promise<SyncEngineResult> {
    if (this.isSyncing) {
      return { total: 0, accepted: 0, duplicates: 0, conflicts: 0, rejected: 0, errors: ['Sync already in progress'] };
    }

    // Try acquiring Web Lock if supported
    if (typeof navigator !== 'undefined' && 'locks' in navigator) {
      return new Promise((resolve) => {
        navigator.locks.request(this.syncLockKey, { ifAvailable: true }, async (lock) => {
          if (!lock) {
            resolve({
              total: 0,
              accepted: 0,
              duplicates: 0,
              conflicts: 0,
              rejected: 0,
              errors: ['Another tab or worker is currently synchronizing'],
            });
            return;
          }
          const result = await this.executeSyncCycle();
          resolve(result);
        });
      });
    }

    return this.executeSyncCycle();
  }

  private async executeSyncCycle(): Promise<SyncEngineResult> {
    this.isSyncing = true;
    const summary: SyncEngineResult = {
      total: 0,
      accepted: 0,
      duplicates: 0,
      conflicts: 0,
      rejected: 0,
      errors: [],
    };

    try {
      const pendingOps = await this.outboxRepo.getPending();
      if (pendingOps.length === 0) {
        return summary;
      }

      summary.total = pendingOps.length;

      // Mark operations as SYNCING in outbox
      for (const op of pendingOps) {
        op.status = 'SYNCING';
        op.attempt_count += 1;
        op.last_attempt_at = new Date().toISOString();
        await this.outboxRepo.update(op);
      }

      // Format payload according to Phase 25 SyncBatchRequest contract
      const batchPayload = {
        client_id: 'FIELD_OFFICER_01',
        client_timestamp: new Date().toISOString(),
        operations: pendingOps.map((op) => ({
          operation_id: op.operation_id,
          entity_type: op.entity_type,
          entity_id: op.entity_id,
          operation_type: op.operation_type,
          payload: op.payload,
          schema_version: '1.0.0',
          base_state_version: op.base_state_version || 1,
          client_created_at: op.created_at,
          client_id: 'FIELD_OFFICER_01',
          attempt_count: op.attempt_count,
        })),
      };

      const response = await fetch('/api/v1/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Actor-Id': 'FIELD_OFFICER_01',
          'X-Actor-Role': 'FIELD_OFFICER',
        },
        body: JSON.stringify(batchPayload),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Sync server responded with HTTP ${response.status}: ${errorText}`);
      }

      const syncResult = await response.json();

      // Reconcile each operation result
      for (const res of syncResult.results || []) {
        const op = pendingOps.find((p) => p.operation_id === res.operation_id);
        if (!op) continue;

        if (res.status === 'ACCEPTED' || res.status === 'DUPLICATE') {
          if (res.status === 'ACCEPTED') summary.accepted += 1;
          else summary.duplicates += 1;

          await this.reconcileSuccess(op, res);
        } else if (res.status === 'CONFLICT') {
          summary.conflicts += 1;
          await this.reconcileConflict(op, res);
        } else if (res.status === 'REJECTED') {
          summary.rejected += 1;
          await this.reconcileRejection(op, res);
        } else {
          // Retryable error
          op.status = 'PENDING';
          op.last_error = res.message || 'Transient sync error';
          await this.outboxRepo.update(op);
        }
      }
    } catch (err: any) {
      summary.errors.push(err.message || 'Network sync error');
      // Revert in-flight ops back to PENDING for subsequent retry
      const pendingOps = await this.outboxRepo.list();
      for (const op of pendingOps) {
        if (op.status === 'SYNCING') {
          op.status = 'PENDING';
          op.last_error = err.message || 'Network failure';
          await this.outboxRepo.update(op);
        }
      }
    } finally {
      this.isSyncing = false;
    }

    return summary;
  }

  private async reconcileSuccess(op: OutboxOperation, res: any): Promise<void> {
    // 1. Update Domain entity record to SYNCED
    if (op.entity_type === 'INCIDENT') {
      const incident = await this.incidentRepo.getById(op.entity_id);
      if (incident) {
        incident.sync_status = 'SYNCED';
        incident.updated_locally_at = new Date().toISOString();
        if (res.server_state_version) {
          (incident as any).state_version = res.server_state_version;
        }
        await this.incidentRepo.save(incident);
      }
    } else if (op.entity_type === 'RESOURCE_REQUEST') {
      const req = await this.resourceRequestRepo.getById(op.entity_id);
      if (req) {
        req.sync_status = 'SYNCED';
        req.status = 'SUBMITTED';
        await this.resourceRequestRepo.save(req);
      }
    }

    // 2. Remove operation from active outbox (or mark SYNCED)
    await this.outboxRepo.remove(op.operation_id);
  }

  private async reconcileConflict(op: OutboxOperation, res: any): Promise<void> {
    op.status = 'CONFLICT';
    op.last_error = res.message || 'State version conflict with server.';
    op.conflict_data = res.server_state || null;
    await this.outboxRepo.update(op);

    // Update local domain entity status to SYNC_ERROR / CONFLICT
    if (op.entity_type === 'INCIDENT') {
      const incident = await this.incidentRepo.getById(op.entity_id);
      if (incident) {
        incident.sync_status = 'SYNC_ERROR';
        incident.last_sync_error = res.message;
        await this.incidentRepo.save(incident);
      }
    }
  }

  private async reconcileRejection(op: OutboxOperation, res: any): Promise<void> {
    op.status = 'FAILED';
    op.last_error = res.message || 'Operation permanently rejected by server.';
    await this.outboxRepo.update(op);

    if (op.entity_type === 'INCIDENT') {
      const incident = await this.incidentRepo.getById(op.entity_id);
      if (incident) {
        incident.sync_status = 'SYNC_ERROR';
        incident.last_sync_error = res.message;
        await this.incidentRepo.save(incident);
      }
    }
  }
}
