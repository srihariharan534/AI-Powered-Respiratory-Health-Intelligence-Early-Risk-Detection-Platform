/**
 * Outbox Repository (Phase 23)
 * Provides durable queuing of operations destined for future Phase 25 synchronization.
 */

import { NexusFieldDatabase } from '../indexeddb/connection';
import {
  STORE_OUTBOX,
  OutboxOperation,
  OutboxEntityType,
  OutboxOperationType,
} from '../types';

export class OutboxRepository {
  private db: NexusFieldDatabase;

  constructor(db: NexusFieldDatabase = NexusFieldDatabase.getInstance()) {
    this.db = db;
  }

  public generateOperationId(): string {
    const timestamp = Date.now();
    const randomPart = Math.random().toString(36).substring(2, 9);
    return `OP-${timestamp}-${randomPart}`;
  }

  public async enqueue<T>(
    entityType: OutboxEntityType,
    entityId: string,
    operationType: OutboxOperationType,
    payload: T
  ): Promise<OutboxOperation<T>> {
    const op: OutboxOperation<T> = {
      operation_id: this.generateOperationId(),
      entity_type: entityType,
      entity_id: entityId,
      operation_type: operationType,
      payload,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      status: 'PENDING',
      attempt_count: 0,
    };

    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_OUTBOX], 'readwrite');
      const store = tx.objectStore(STORE_OUTBOX);
      const request = store.put(op);

      request.onsuccess = () => resolve(op);
      request.onerror = () => reject(request.error || new Error('Failed to enqueue outbox operation.'));
    });
  }

  public async getPending(): Promise<OutboxOperation[]> {
    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_OUTBOX], 'readonly');
      const store = tx.objectStore(STORE_OUTBOX);
      const index = store.index('status');
      const request = index.getAll('PENDING');

      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error || new Error('Failed to get pending outbox operations.'));
    });
  }

  public async list(): Promise<OutboxOperation[]> {
    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_OUTBOX], 'readonly');
      const store = tx.objectStore(STORE_OUTBOX);
      const request = store.getAll();

      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error || new Error('Failed to list outbox operations.'));
    });
  }

  public async getById(operationId: string): Promise<OutboxOperation | null> {
    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_OUTBOX], 'readonly');
      const store = tx.objectStore(STORE_OUTBOX);
      const request = store.get(operationId);

      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(request.error || new Error('Failed to get outbox operation by ID.'));
    });
  }

  public async update(operation: OutboxOperation): Promise<void> {
    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_OUTBOX], 'readwrite');
      const store = tx.objectStore(STORE_OUTBOX);
      const request = store.put(operation);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error || new Error('Failed to update outbox operation.'));
    });
  }

  public async remove(operationId: string): Promise<void> {
    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_OUTBOX], 'readwrite');
      const store = tx.objectStore(STORE_OUTBOX);
      const request = store.delete(operationId);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error || new Error('Failed to remove outbox operation.'));
    });
  }

  public async clearAll(): Promise<void> {
    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_OUTBOX], 'readwrite');
      const store = tx.objectStore(STORE_OUTBOX);
      const request = store.clear();

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error || new Error('Failed to clear outbox.'));
    });
  }
}
