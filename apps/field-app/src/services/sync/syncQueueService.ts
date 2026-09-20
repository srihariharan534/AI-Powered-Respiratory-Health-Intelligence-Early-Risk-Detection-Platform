/**
 * Durable Synchronization Queue Service (Phase 23)
 * Bridges in-memory reactivity with durable IndexedDB Outbox storage.
 * Ensures offline actions, reports, and requests survive browser restarts and page refreshes.
 */

import { PendingSyncItem } from '../../types';
import { OutboxRepository } from '../../database/repositories/OutboxRepository';
import { OutboxEntityType } from '../../database/types';
import { BackgroundSyncManager } from '../../service-worker/background-sync';

export class SyncQueueService {
  private static queue: PendingSyncItem[] = [];
  private static listeners: Set<(items: PendingSyncItem[]) => void> = new Set();
  private static lastSuccessfulSync: string | null = null;
  private static outboxRepo: OutboxRepository = new OutboxRepository();

  /**
   * Initializes queue by loading existing durable pending operations from IndexedDB.
   */
  public static async initialize(): Promise<void> {
    try {
      const pendingOps = await this.outboxRepo.getPending();
      this.queue = pendingOps.map((op) => ({
        queue_id: op.operation_id,
        entity_type: op.entity_type,
        payload: op.payload,
        queued_at: op.created_at,
        status: op.status === 'PENDING' ? 'QUEUED' : op.status === 'SYNCING' ? 'SYNCING' : 'ERROR',
        error_message: op.last_error,
      }));
      this.notify();
    } catch (err) {
      console.warn('Could not initialize SyncQueue from IndexedDB (may be in non-browser env):', err);
    }
  }

  public static enqueue(
    entityType: OutboxEntityType,
    payload: any
  ): PendingSyncItem {
    const queueId = this.outboxRepo.generateOperationId();
    const item: PendingSyncItem = {
      queue_id: queueId,
      entity_type: entityType,
      payload,
      queued_at: new Date().toISOString(),
      status: 'QUEUED',
    };

    this.queue.push(item);
    this.notify();

    // Persist to durable outbox asynchronously
    this.outboxRepo
      .enqueue(
        entityType,
        payload.incident_id || payload.request_id || payload.assignment_id || queueId,
        'CREATE',
        payload
      )
      .then(() => {
        // Trigger Background Sync registration if supported
        BackgroundSyncManager.getInstance().registerOutboxSync().catch(() => {});
      })
      .catch((err) => {
        console.warn('Failed to persist outbox operation to IndexedDB:', err);
      });

    return { ...item };
  }

  public static getPending(): PendingSyncItem[] {
    return [...this.queue];
  }

  public static getCount(): number {
    return this.queue.length;
  }

  public static getLastSuccessfulSync(): string | null {
    return this.lastSuccessfulSync;
  }

  public static async triggerSync(): Promise<any> {
    const { ClientSyncEngine } = await import('./clientSyncEngine');
    const engine = ClientSyncEngine.getInstance();
    const result = await engine.sync();
    // Refresh queue from IndexedDB
    await this.initialize();
    if (result.accepted > 0 || result.duplicates > 0) {
      this.lastSuccessfulSync = new Date().toISOString();
    }
    return result;
  }

  public static markAllSynced(): void {
    this.queue = [];
    this.lastSuccessfulSync = new Date().toISOString();
    this.notify();
  }

  public static clearQueue(): void {
    this.queue = [];
    this.notify();
    this.outboxRepo.clearAll().catch((err) => {
      console.warn('Failed to clear outbox from IndexedDB:', err);
    });
  }

  public static subscribe(listener: (items: PendingSyncItem[]) => void): () => void {
    this.listeners.add(listener);
    listener([...this.queue]);
    return () => this.listeners.delete(listener);
  }

  private static notify(): void {
    this.listeners.forEach((l) => l([...this.queue]));
  }
}
