/**
 * Database Connection & Lifecycle Manager (Phase 23)
 * Manages opening IndexedDB connection, executing versioned migrations,
 * and handling transactional lifecycles.
 */

import { DB_NAME, DB_VERSION } from '../types';
import { runMigrationV1 } from '../migrations/v1';

export class NexusFieldDatabase {
  private static instance: NexusFieldDatabase | null = null;
  private dbPromise: Promise<IDBDatabase> | null = null;

  private constructor() {}

  public static getInstance(): NexusFieldDatabase {
    if (!this.instance) {
      this.instance = new NexusFieldDatabase();
    }
    return this.instance;
  }

  public isSupported(): boolean {
    return typeof indexedDB !== 'undefined';
  }

  public async getDatabase(): Promise<IDBDatabase> {
    if (this.dbPromise) {
      return this.dbPromise;
    }

    if (!this.isSupported()) {
      throw new Error('IndexedDB is not supported on this platform/environment.');
    }

    this.dbPromise = new Promise<IDBDatabase>((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = (event: IDBVersionChangeEvent) => {
        const db = request.result;
        const oldVersion = event.oldVersion;

        if (oldVersion < 1) {
          runMigrationV1(db);
        }
      };

      request.onsuccess = () => {
        const db = request.result;
        db.onversionchange = () => {
          db.close();
          this.dbPromise = null;
        };
        resolve(db);
      };

      request.onerror = () => {
        this.dbPromise = null;
        reject(request.error || new Error('Failed to open IndexedDB.'));
      };

      request.onblocked = () => {
        console.warn('IndexedDB open blocked by open tabs.');
      };
    });

    return this.dbPromise;
  }

  public async close(): Promise<void> {
    if (this.dbPromise) {
      const db = await this.dbPromise;
      db.close();
      this.dbPromise = null;
    }
  }

  /**
   * Development & test helper ONLY.
   * Completely purges the local database. Never invoked during normal field operation.
   */
  public async resetDatabaseForTesting(): Promise<void> {
    await this.close();
    return new Promise((resolve, reject) => {
      const request = indexedDB.deleteDatabase(DB_NAME);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
      request.onblocked = () => resolve();
    });
  }
}
