/**
 * App State Repository (Phase 23)
 * Provides durable key-value persistence for client settings and runtime state.
 */

import { NexusFieldDatabase } from '../indexeddb/connection';
import { STORE_APP_STATE, AppStateRecord } from '../types';

export class AppStateRepository {
  private db: NexusFieldDatabase;

  constructor(db: NexusFieldDatabase = NexusFieldDatabase.getInstance()) {
    this.db = db;
  }

  public async set<T>(key: string, value: T): Promise<void> {
    const record: AppStateRecord = {
      key,
      value,
      updated_at: new Date().toISOString(),
    };

    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_APP_STATE], 'readwrite');
      const store = tx.objectStore(STORE_APP_STATE);
      const request = store.put(record);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error || new Error('Failed to set app state.'));
    });
  }

  public async get<T>(key: string): Promise<T | null> {
    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_APP_STATE], 'readonly');
      const store = tx.objectStore(STORE_APP_STATE);
      const request = store.get(key);

      request.onsuccess = () => {
        if (request.result) {
          resolve(request.result.value as T);
        } else {
          resolve(null);
        }
      };
      request.onerror = () => reject(request.error || new Error('Failed to get app state.'));
    });
  }
}
