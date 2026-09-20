/**
 * Assignment Repository (Phase 23)
 * Provides durable operations for caching and updating field assignments.
 */

import { NexusFieldDatabase } from '../indexeddb/connection';
import { STORE_ASSIGNMENTS, DurableAssignment } from '../types';

export class AssignmentRepository {
  private db: NexusFieldDatabase;

  constructor(db: NexusFieldDatabase = NexusFieldDatabase.getInstance()) {
    this.db = db;
  }

  public async save(assignment: DurableAssignment): Promise<DurableAssignment> {
    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_ASSIGNMENTS], 'readwrite');
      const store = tx.objectStore(STORE_ASSIGNMENTS);
      const request = store.put(assignment);

      request.onsuccess = () => resolve(assignment);
      request.onerror = () => reject(request.error || new Error('Failed to save assignment.'));
    });
  }

  public async getById(assignmentId: string): Promise<DurableAssignment | null> {
    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_ASSIGNMENTS], 'readonly');
      const store = tx.objectStore(STORE_ASSIGNMENTS);
      const request = store.get(assignmentId);

      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(request.error || new Error('Failed to get assignment.'));
    });
  }

  public async list(): Promise<DurableAssignment[]> {
    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_ASSIGNMENTS], 'readonly');
      const store = tx.objectStore(STORE_ASSIGNMENTS);
      const request = store.getAll();

      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error || new Error('Failed to list assignments.'));
    });
  }
}
