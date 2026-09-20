/**
 * Resource Request Repository (Phase 23)
 * Provides durable operations for tactical resource requisitions.
 */

import { NexusFieldDatabase } from '../indexeddb/connection';
import { STORE_RESOURCE_REQUESTS, DurableResourceRequest } from '../types';

export class ResourceRequestRepository {
  private db: NexusFieldDatabase;

  constructor(db: NexusFieldDatabase = NexusFieldDatabase.getInstance()) {
    this.db = db;
  }

  public async save(request: DurableResourceRequest): Promise<DurableResourceRequest> {
    if (!request.request_id) {
      throw new Error('Validation Error: request_id is required.');
    }
    if (!request.reason || !request.reason.trim()) {
      throw new Error('Validation Error: reason is required.');
    }

    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_RESOURCE_REQUESTS], 'readwrite');
      const store = tx.objectStore(STORE_RESOURCE_REQUESTS);
      const req = store.put(request);

      req.onsuccess = () => resolve(request);
      req.onerror = () => reject(req.error || new Error('Failed to save resource request.'));
    });
  }

  public async getById(requestId: string): Promise<DurableResourceRequest | null> {
    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_RESOURCE_REQUESTS], 'readonly');
      const store = tx.objectStore(STORE_RESOURCE_REQUESTS);
      const req = store.get(requestId);

      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => reject(req.error || new Error('Failed to get resource request.'));
    });
  }

  public async list(): Promise<DurableResourceRequest[]> {
    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_RESOURCE_REQUESTS], 'readonly');
      const store = tx.objectStore(STORE_RESOURCE_REQUESTS);
      const req = store.getAll();

      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => reject(req.error || new Error('Failed to list resource requests.'));
    });
  }
}
