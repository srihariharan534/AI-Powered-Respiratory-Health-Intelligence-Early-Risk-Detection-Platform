/**
 * Incident Repository (Phase 23)
 * Provides durable CRUD operations for incidents stored in IndexedDB.
 */

import { NexusFieldDatabase } from '../indexeddb/connection';
import { STORE_INCIDENTS, DurableIncident, LocalSyncStatus } from '../types';
import { DataValidator } from '../../services/validation/validator';

export class IncidentRepository {
  private db: NexusFieldDatabase;

  constructor(db: NexusFieldDatabase = NexusFieldDatabase.getInstance()) {
    this.db = db;
  }

  public async save(incident: DurableIncident): Promise<DurableIncident> {
    DataValidator.validateIncident(incident);

    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_INCIDENTS], 'readwrite');
      const store = tx.objectStore(STORE_INCIDENTS);
      const request = store.put(incident);

      request.onsuccess = () => resolve(incident);
      request.onerror = () => reject(request.error || new Error('Failed to save incident.'));
    });
  }

  public async getById(incidentId: string): Promise<DurableIncident | null> {
    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_INCIDENTS], 'readonly');
      const store = tx.objectStore(STORE_INCIDENTS);
      const request = store.get(incidentId);

      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(request.error || new Error('Failed to get incident.'));
    });
  }

  public async list(): Promise<DurableIncident[]> {
    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_INCIDENTS], 'readonly');
      const store = tx.objectStore(STORE_INCIDENTS);
      const request = store.getAll();

      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error || new Error('Failed to list incidents.'));
    });
  }

  public async listBySyncStatus(status: LocalSyncStatus): Promise<DurableIncident[]> {
    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_INCIDENTS], 'readonly');
      const store = tx.objectStore(STORE_INCIDENTS);
      const index = store.index('sync_status');
      const request = index.getAll(status);

      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error || new Error('Failed to list incidents by sync status.'));
    });
  }

  public async updateSyncStatus(
    incidentId: string,
    status: LocalSyncStatus,
    lastError?: string
  ): Promise<void> {
    const incident = await this.getById(incidentId);
    if (!incident) {
      throw new Error(`Incident ${incidentId} not found.`);
    }

    incident.sync_status = status;
    incident.updated_locally_at = new Date().toISOString();
    if (lastError !== undefined) {
      incident.last_sync_error = lastError;
      incident.sync_attempts += 1;
    }

    await this.save(incident);
  }

  public async delete(incidentId: string): Promise<void> {
    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_INCIDENTS], 'readwrite');
      const store = tx.objectStore(STORE_INCIDENTS);
      const request = store.delete(incidentId);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error || new Error('Failed to delete incident.'));
    });
  }
}
